"""T7: validate import provenance and quarantine forum/video hypotheses.

Passing this gate establishes metadata eligibility, not factual verification.
No writes, model calls or network requests occur in this module.
"""
from __future__ import annotations

from collections import defaultdict
import csv
from dataclasses import asdict, dataclass, field
from pathlib import Path
import re
import sqlite3
from typing import Iterable

from backend.app.core.config import MAPPING_PATH
from backend.app.services.mapping import Mapping, load_mapping
from backend.app.services.pages import parse_page_refs

HYPOTHESIS_FLAG = 'HYPOTHESIS_NEEDS_VALIDATION'
DRAFT_STATUS = 'DRAFT_NOT_RELEASED'
RESTRICTED_SOURCE_TYPES = {'FORUM', 'VIDEO'}
EMPTY_VALUES = {'', '-', '—', 'n/a', 'na', 'none', 'null', 'nan', 'unknown', 'tbd', '[]', '{}', 'chưa có'}

# CSV exports use both REPO_* names and canonical workbook columns.
ALIASES = {
    'knowledge_id': ('Knowledge_ID', 'Canonical_ID'),
    'text': ('Canonical_Knowledge', 'Knowledge_Text', 'Statement'),
    'source_id': ('Source_ID', 'Source_IDs'),
    'source_type': ('Source_Type',),
    'pdf_pages_raw': ('PDF_Pages', 'Source_Pages'),
    'author_stance': ('Author_Stances', 'Author_Stance'),
    'school': ('School', 'School_Label', 'Truong_Phai'),
    'validation_example': ('Validation_Example', 'Example', 'Case_Example', 'Case_ID', 'Validation_Case_ID'),
    'original_id': ('Original_Canonical_ID',),
    'active_id': ('Active_Canonical_ID',),
}


def clean(value) -> str:
    if value is None:
        return ''
    result = str(value).strip()
    return '' if result.casefold() in EMPTY_VALUES else result


def tokens(value) -> list[str]:
    return [part.strip() for part in re.split(r'[;,|]', clean(value)) if part.strip()]


def has_flag(value, flag: str = HYPOTHESIS_FLAG) -> bool:
    return flag in {part.upper() for part in tokens(value)}


def is_source_d_type(value) -> bool:
    return bool({part.upper() for part in tokens(value)} & RESTRICTED_SOURCE_TYPES)


def _key(value: str) -> str:
    return str(value).strip().casefold().replace(' ', '_')


def normalize_record(record: dict, mapping: Mapping | None = None, section: str | None = None) -> dict:
    aliases = {_key(alias): target for target, names in ALIASES.items() for alias in names}
    if mapping and section in mapping.sections:
        aliases.update({_key(column): field for field, column in mapping.sections[section].columns.items()})
    result = {}
    for key, value in record.items():
        target = aliases.get(_key(key), _key(key))
        if target in result and clean(result[target]) and clean(value) and clean(result[target]) != clean(value):
            raise ValueError(f'Conflicting aliases for field {target}.')
        if target not in result or clean(value):
            result[target] = value
    return result


@dataclass(frozen=True)
class GateError:
    code: str
    message: str
    knowledge_id: str = ''
    row: int | None = None
    origin: str = ''


@dataclass
class GateReport:
    checked: int = 0
    new_records: int = 0
    quarantined_ids: list[str] = field(default_factory=list)
    errors: list[GateError] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict:
        return {'status': 'PASSED' if self.ok else 'FAILED', **asdict(self)}

    def require_valid(self) -> None:
        if not self.ok:
            first = self.errors[0]
            raise ValueError(f'Knowledge gate: {len(self.errors)} error(s); '
                             f'{first.origin}:{first.row} {first.knowledge_id} [{first.code}] {first.message}')


def _positive_page(value) -> bool:
    text = clean(value)
    # Excel page numbers may be represented as 12.0 by pandas.
    return bool(re.fullmatch(r'[0-9]+(?:\.0+)?', text)) and float(text) > 0


def _direct_pages_valid(record: dict, mapping: Mapping) -> bool:
    value = record.get('pdf_pages_raw')
    raw = str(int(value)) if isinstance(value, float) and value.is_integer() else clean(value)
    if not raw:
        return False
    parts = [part.strip() for part in raw.split(mapping.page_parsing.get('separator', ';'))]
    parsed = parse_page_refs(raw, clean(record.get('book_code')), mapping)
    return (len(parsed) == len(parts) and bool(parts)
            and all(ref.pdf_page is not None and ref.pdf_page > 0
                    and (ref.part_number is None or int(ref.part_number) > 0) for ref in parsed))


def validate_records(
    knowledge: Iterable[dict], sources: Iterable[dict] = (), evidence: Iterable[dict] = (),
    *, redirects: dict[str, str] | None = None, existing_ids: Iterable[str] = (),
    mapping: Mapping | None = None,
) -> GateReport:
    """Require >=1 basis for NEW ids; source-D rules always apply, including updates."""
    mapping = mapping or load_mapping(MAPPING_PATH)
    rows = [normalize_record(r) for r in knowledge]
    sources = [normalize_record(r) for r in sources]
    evidence = [normalize_record(r) for r in evidence]
    existing_ids = set(existing_ids)
    redirects = redirects or {}
    report = GateReport(checked=len(rows))

    def error(code: str, message: str, row: dict, kid: str = '') -> None:
        report.errors.append(GateError(code, message, kid or clean(row.get('knowledge_id')),
                                       row.get('_row'), clean(row.get('_origin'))))

    source_index = {}
    for row in sources:
        sid = clean(row.get('source_id'))
        if not sid:
            error('missing_source_id', 'Source must have Source_ID.', row)
        elif sid in source_index:
            error('duplicate_source', f'Duplicate Source_ID {sid}.', row)
        else:
            source_index[sid] = row
    ids = set()
    for row in rows:
        kid = clean(row.get('knowledge_id'))
        if not kid:
            error('missing_id', 'Knowledge must have Knowledge_ID/Canonical_ID.', row)
        elif kid in ids:
            error('duplicate_id', 'Knowledge id occurs more than once.', row)
        ids.add(kid)
        if not clean(row.get('text')):
            error('missing_text', 'Knowledge text is required.', row)

    def resolve(kid: str, row: dict) -> str:
        seen = set()
        while kid in redirects:
            if kid in seen:
                error('redirect_cycle', 'Evidence redirect contains a cycle.', row)
                break
            seen.add(kid)
            kid = clean(redirects[kid])
        return kid

    ev_by_id = defaultdict(list)
    for row in evidence:
        kid = resolve(clean(row.get('knowledge_id')), row)
        if not kid or kid not in ids | existing_ids:
            error('unknown_knowledge', 'Evidence must resolve to a knowledge id in this import or baseline.', row)
        ev_by_id[kid].append(row)

    def linked_sources(row: dict, kid: str) -> list[dict]:
        found = []
        for sid in tokens(row.get('source_id')):
            source = source_index.get(sid)
            if source is None:
                error('unknown_source', f'Source_ID {sid} is absent from source registry.', row, kid)
            else:
                found.append(source)
        return found

    for row in rows:
        kid = clean(row.get('knowledge_id'))
        row_sources = linked_sources(row, kid)
        linked_ev = ev_by_id[kid]
        all_sources = list(row_sources)
        valid_evidence = bool(row_sources) and _direct_pages_valid(row, mapping)
        for ev in linked_ev:
            ev_sources = linked_sources(ev, kid) if clean(ev.get('source_id')) else row_sources
            all_sources.extend(ev_sources)
            needs_part = clean(row.get('book_code')) == 'BD' or any(clean(s.get('book_code')) == 'BD' for s in ev_sources)
            if ev_sources and _positive_page(ev.get('pdf_page')) and (not needs_part or _positive_page(ev.get('part_number'))):
                valid_evidence = True
        # Missing direct ids must not hide a D source registered for this book.
        if not clean(row.get('source_id')) and clean(row.get('book_code')):
            all_sources.extend(s for s in sources if clean(s.get('book_code')) == clean(row['book_code']))
        restricted = (is_source_d_type(row.get('source_type'))
                      or any(is_source_d_type(s.get('source_type')) for s in all_sources)
                      or any(is_source_d_type(ev.get('source_type')) for ev in linked_ev))
        if kid not in existing_ids:
            report.new_records += 1
            if not (valid_evidence or clean(row.get('school')) or clean(row.get('author_stance'))
                    or clean(row.get('validation_example'))):
                error('missing_basis', 'New knowledge needs source+positive PDF page, a school/Author_Stances, '
                      'or a validation example/case.', row)
        if restricted:
            report.quarantined_ids.append(kid)
            if clean(row.get('release_status')).upper() != DRAFT_STATUS:
                error('source_d_release', f'FORUM/VIDEO requires Release_Status={DRAFT_STATUS}.', row)
            if not has_flag(row.get('review_flag')):
                error('source_d_review', f'FORUM/VIDEO requires Review_Flag token {HYPOTHESIS_FLAG}.', row)
    report.quarantined_ids = sorted(set(report.quarantined_ids))
    return report


def _csv_rows(path: Path, mapping: Mapping) -> tuple[str | None, list[dict]]:
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle, strict=True)
        if not reader.fieldnames or len({_key(h) for h in reader.fieldnames}) != len(reader.fieldnames):
            raise ValueError(f'{path}: missing or duplicate CSV headers.')
        headers = normalize_record(dict.fromkeys(reader.fieldnames), mapping)
        name = path.stem.upper()
        if name in {'REPO_EVIDENCE', 'EVIDENCE'} or 'evidence_id' in headers:
            section = 'evidence'
        elif name in {'CANONICAL_ID_REDIRECTS', 'REPO_ID_REDIRECTS'} or 'original_id' in headers:
            section = 'id_redirects'
        elif name in {'REPO_SOURCE', 'REPO_SOURCES', 'SOURCES'} or ('source_id' in headers and 'title' in headers and 'text' not in headers):
            section = 'sources'
        elif name.startswith('REPO_KNOWLEDGE') or name in {'CANONICAL_KNOWLEDGE', 'CANONICAL_KNOWLEDGE_V1_0'} or 'knowledge_id' in headers or 'text' in headers:
            section = 'knowledge_items'
        else:
            return None, []
        rows = []
        for row in reader:
            if None in row:
                raise ValueError(f'{path}:{reader.line_num}: too many fields in CSV row.')
            if any(clean(v) for v in row.values()):
                rows.append({**normalize_record(row, mapping, section), '_row': reader.line_num, '_origin': str(path)})
        return section, rows


def _excel_rows(path: Path, mapping: Mapping) -> dict[str, list[dict]]:
    # pandas/openpyxl are needed only for Excel, not the CSV validation CLI.
    import pandas as pd
    result = {}
    with pd.ExcelFile(path) as workbook:
        for section in ('knowledge_items', 'sources', 'evidence', 'id_redirects'):
            spec = mapping.sections[section]
            if spec.sheet not in workbook.sheet_names:
                if section in {'knowledge_items', 'sources'}:
                    raise ValueError(f'Missing sheet {spec.sheet}.')
                result[section] = []
                continue
            frame = pd.read_excel(workbook, sheet_name=spec.sheet)
            result[section] = [
                {**normalize_record(row, mapping, section), '_row': index + 2, '_origin': f'{path}:{spec.sheet}'}
                for index, row in enumerate(frame.to_dict('records')) if any(clean(v) for v in row.values())
            ]
    return result


def validate_path(path: str | Path, *, mapping: Mapping | None = None,
                  existing_ids: Iterable[str] = ()) -> GateReport:
    path = Path(path)
    mapping = mapping or load_mapping(MAPPING_PATH)
    try:
        if not path.exists():
            raise FileNotFoundError(f'Input does not exist: {path}')
        if path.suffix.lower() in {'.xlsx', '.xlsm'} and path.is_file():
            sections = _excel_rows(path, mapping)
        else:
            if path.is_dir():
                files = sorted(p for p in path.iterdir() if p.is_file() and p.suffix.lower() == '.csv')
            elif path.suffix.lower() == '.csv':
                # A single knowledge CSV can use sibling source/evidence registries.
                files = [path] + sorted(p for p in path.parent.glob('*.csv')
                                       if p != path and p.stem.upper() in {
                                           'REPO_SOURCE', 'REPO_SOURCES', 'SOURCES', 'REPO_EVIDENCE',
                                           'EVIDENCE', 'CANONICAL_ID_REDIRECTS', 'REPO_ID_REDIRECTS'})
            else:
                raise ValueError('Expected a CSV directory, CSV file, or .xlsx/.xlsm workbook.')
            sections = defaultdict(list)
            for file in files:
                section, rows = _csv_rows(file, mapping)
                if section:
                    sections[section].extend(rows)
        if not sections.get('knowledge_items'):
            raise ValueError('No knowledge records found; an empty input is not a passing gate.')
        redirects = {clean(r.get('original_id')): clean(r.get('active_id'))
                     for r in sections.get('id_redirects', [])}
        return validate_records(sections['knowledge_items'], sections.get('sources', []),
                                sections.get('evidence', []), redirects=redirects,
                                existing_ids=existing_ids, mapping=mapping)
    except (OSError, ValueError, KeyError, csv.Error, ImportError) as exc:
        return GateReport(errors=[GateError('input_error', str(exc), origin=str(path))])


def existing_knowledge_ids(path: str | Path) -> set[str]:
    """Read an explicitly selected baseline database without creating or changing it."""
    path = Path(path).resolve()
    with sqlite3.connect(f'{path.as_uri()}?mode=ro', uri=True) as connection:
        return {row[0] for row in connection.execute('SELECT knowledge_id FROM knowledge_items')}
