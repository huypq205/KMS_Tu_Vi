"""T7: provenance alternatives, source-D quarantine and import/index integration."""
from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.core.config import MAPPING_PATH
from backend.app.db.models import Base, Book, Chunk, ChunkMember, Evidence, KnowledgeItem
from backend.app.services.mapping import load_mapping
from backend.app.services.tiering import assign_tier
from backend.app.services.knowledge_gate import validate_records, validate_path
from scripts import import_excel

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/knowledge_gate/valid'
SOURCES = [{'source_id': 'SRC', 'book_code': 'NPL', 'source_type': 'BOOK'}]


def claim(**extra):
    return {'knowledge_id': 'K1', 'book_code': 'NPL', 'source_id': 'SRC',
            'text': 'Synthetic claim, not canonical knowledge.', **extra}


def codes(report):
    return {error.code for error in report.errors}


def test_valid_csv_fixture_passes_all_three_alternatives_and_quarantine():
    report = validate_path(FIXTURE)
    assert report.ok
    assert report.checked == report.new_records == 4
    assert report.quarantined_ids == ['K-VIDEO']


@pytest.mark.parametrize('extra', [
    {'pdf_pages_raw': '12'}, {'author_stance': 'School A'},
    {'school': 'School B'}, {'validation_example': 'CASE-TEST-01'},
])
def test_at_least_one_element_is_sufficient(extra):
    assert validate_records([claim(**extra)], SOURCES).ok


@pytest.mark.parametrize('value', ['', ' ', 'N/A', 'UNKNOWN', '[]', '{}', 'TBD', '—'])
def test_missing_all_elements_or_placeholder_is_rejected(value):
    report = validate_records([claim(author_stance=value, validation_example=value)], SOURCES)
    assert not report.ok
    assert 'missing_basis' in codes(report)


@pytest.mark.parametrize('page', ['0', '-1', 'abc', '12;invalid', '1.5'])
def test_invalid_pages_do_not_count_as_evidence(page):
    assert 'missing_basis' in codes(validate_records([claim(pdf_pages_raw=page)], SOURCES))


def test_evidence_must_resolve_both_source_and_knowledge():
    evidence = [{'knowledge_id': 'K1', 'source_id': 'SRC', 'pdf_page': '12'}]
    assert validate_records([claim()], SOURCES, evidence).ok
    bad = deepcopy(evidence)
    bad[0]['source_id'] = 'MISSING'
    report = validate_records([claim()], SOURCES, bad)
    assert {'unknown_source', 'missing_basis'} <= codes(report)
    bad = deepcopy(evidence)
    bad[0]['knowledge_id'] = 'OTHER'
    assert 'unknown_knowledge' in codes(validate_records([claim()], SOURCES, bad))


def test_redirected_evidence_and_bd_part_pages():
    sources = [{'source_id': 'BD-SRC', 'book_code': 'BD', 'source_type': 'BOOK'}]
    row = claim(book_code='BD', source_id='BD-SRC')
    ev = [{'knowledge_id': 'OLD', 'source_id': 'BD-SRC', 'pdf_page': 36, 'part_number': 7}]
    assert validate_records([row], sources, ev, redirects={'OLD': 'K1'}).ok
    assert validate_records([claim(book_code='BD', source_id='BD-SRC', pdf_pages_raw='P7:36')], sources).ok
    ev[0].pop('part_number')
    assert 'missing_basis' in codes(validate_records([row], sources, ev, redirects={'OLD': 'K1'}))


def test_excel_numeric_pages_and_conflicting_source_aliases(tmp_path):
    path = tmp_path / 'numeric.xlsx'
    write_workbook(path, [claim(pdf_pages_raw=12.0)])
    assert validate_path(path).ok
    csv_path = tmp_path / 'REPO_KNOWLEDGE.csv'
    csv_path.write_text('Knowledge_ID,Canonical_Knowledge,Source_ID,Source_IDs,School\n'
                        'K1,Synthetic,SRC1,SRC2,School A\n', encoding='utf-8')
    assert 'input_error' in codes(validate_path(csv_path))


def test_gate_only_requires_basis_for_new_ids_but_never_exempts_source_d():
    assert validate_records([claim()], SOURCES, existing_ids={'K1'}).ok
    video = [{**SOURCES[0], 'source_type': 'VIDEO'}]
    report = validate_records([claim(release_status='LOCKED')], video, existing_ids={'K1'})
    assert 'source_d_release' in codes(report)
    assert 'source_d_review' in codes(report)


@pytest.mark.parametrize('source_type', ['FORUM', 'VIDEO', 'forum', 'video'])
def test_source_d_cannot_be_released(source_type):
    sources = [{**SOURCES[0], 'source_type': source_type}]
    row = claim(author_stance='School A', release_status='LOCKED', review_flag='HYPOTHESIS_NEEDS_VALIDATION')
    assert 'source_d_release' in codes(validate_records([row], sources))
    row.update(release_status='DRAFT_NOT_RELEASED')
    assert validate_records([row], sources).ok
    row['review_flag'] = 'NOT_HYPOTHESIS_NEEDS_VALIDATION'
    assert 'source_d_review' in codes(validate_records([row], sources))


def test_mixed_sources_and_evidence_cannot_hide_source_d():
    sources = SOURCES + [{'source_id': 'VID', 'source_type': 'VIDEO'}]
    row = claim(source_id='SRC;VID', author_stance='School A', release_status='LOCKED')
    assert 'source_d_release' in codes(validate_records([row], sources))
    row['source_id'] = 'SRC'
    ev = [{'knowledge_id': 'K1', 'source_id': 'VID', 'pdf_page': 12}]
    assert 'source_d_release' in codes(validate_records([row], sources, ev))


def test_source_d_and_hypothesis_override_book_tier_and_custom_rules():
    mapping = deepcopy(load_mapping(MAPPING_PATH))
    mapping.trust_tiers['rules'].insert(0, {'tier': 1, 'when': {}})
    for extra in ({'source_type': 'VIDEO'}, {'source_type': 'FORUM'},
                  {'review_flag': 'OTHER;HYPOTHESIS_NEEDS_VALIDATION'}):
        assert assign_tier({'book_code': 'NPL', **extra}, mapping) == 9
    assert assign_tier({'book_code': 'NPL'}, load_mapping(MAPPING_PATH)) == 1


def test_duplicates_unknown_sources_and_missing_identity_fail():
    assert 'duplicate_id' in codes(validate_records([claim(school='A'), claim(school='B')], SOURCES))
    assert 'unknown_source' in codes(validate_records([claim(source_id='typo', school='A')], SOURCES))
    assert 'missing_id' in codes(validate_records([claim(knowledge_id='', school='A')], SOURCES))


def write_workbook(path, rows, source_rows=None):
    mapping = load_mapping(MAPPING_PATH)
    frames = {'knowledge_items': rows, 'sources': source_rows or SOURCES, 'evidence': [], 'id_redirects': []}
    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        for name, records in frames.items():
            section = mapping.sections[name]
            frame = pd.DataFrame(records, columns=list(section.columns))
            frame.rename(columns=section.columns).to_excel(writer, sheet_name=section.sheet, index=False)


def test_excel_gate_uses_existing_column_mapping(tmp_path):
    path = tmp_path / 'sample.xlsx'
    write_workbook(path, [claim(author_stance='School A')])
    assert validate_path(path).ok
    write_workbook(path, [claim()])
    assert 'missing_basis' in codes(validate_path(path))


def test_gate_cli_reports_row_and_returns_nonzero(tmp_path):
    path = tmp_path / 'REPO_KNOWLEDGE.csv'
    path.write_text('Knowledge_ID,Canonical_Knowledge\nBAD,Synthetic test\n', encoding='utf-8')
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/validate_knowledge_import.py'), str(path), '--json'],
                            capture_output=True, text=True, encoding='utf-8')
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report['errors'][0]['knowledge_id'] == 'BAD'
    assert report['errors'][0]['row'] == 2
    assert report['status'] == 'FAILED'


@pytest.mark.parametrize('empty', [False, True])
def test_missing_input_or_empty_directory_does_not_silently_pass(tmp_path, empty):
    path = tmp_path if empty else tmp_path / 'missing'
    assert not validate_path(path).ok


def test_import_gate_rejects_before_initializing_database(tmp_path, monkeypatch):
    path = tmp_path / 'bad.xlsx'
    write_workbook(path, [claim()])
    monkeypatch.setattr(sys, 'argv', ['import_excel.py', '--excel', str(path), '--gate'])
    monkeypatch.setattr(import_excel, 'DB_PATH', tmp_path / 'absent.db')
    with patch.object(import_excel, 'init_db') as init:
        assert import_excel.main() == 1
        init.assert_not_called()


@pytest.fixture
def isolated_db(tmp_path):
    engine = create_engine(f'sqlite:///{tmp_path / "gate.db"}')
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def test_import_source_d_is_tier9_even_without_gate_and_not_indexed(tmp_path, isolated_db):
    path = tmp_path / 'video.xlsx'
    video = [{**SOURCES[0], 'source_type': 'VIDEO'}]
    row = claim(pdf_pages_raw='12', author_stance='School A', release_status='DRAFT_NOT_RELEASED',
                review_flag='HYPOTHESIS_NEEDS_VALIDATION')
    write_workbook(path, [row], video)
    mapping = load_mapping(MAPPING_PATH)
    import_excel.import_books(isolated_db, path, mapping)
    stats = import_excel.import_knowledge(isolated_db, path, mapping)
    isolated_db.flush()
    assert stats['tier_counts'] == {9: 1}
    assert isolated_db.get(KnowledgeItem, 'K1').trust_tier == 9
    # Defense in depth: even a wrong tier or configuration enabling 9 cannot index it.
    isolated_db.get(KnowledgeItem, 'K1').trust_tier = 1
    isolated_db.add(Evidence(evidence_id='EV1', knowledge_id='K1', pdf_page=12))
    isolated_db.flush()
    from backend.app.services import chunker
    unsafe_mapping = deepcopy(mapping)
    unsafe_mapping.trust_tiers['enabled_tiers'] = [1, 2, 3, 9]

    @contextmanager
    def scope():
        yield isolated_db

    with patch.object(chunker, 'session_scope', scope), patch.object(chunker, 'load_mapping', return_value=unsafe_mapping):
        assert chunker.build_chunks() == []


def test_import_invalid_gate_preserves_existing_data_and_chunks(tmp_path, isolated_db):
    path = tmp_path / 'bad.xlsx'
    write_workbook(path, [claim()])
    isolated_db.add(KnowledgeItem(knowledge_id='KEEP', book_code='NPL', text='Keep me',
                                 trust_tier=1, content_hash='hash'))
    isolated_db.add(Chunk(chunk_id='CK-KEEP', book_code='NPL', chunk_text='Keep chunk', embed_text='',
                          trust_tier=1, chunking_version='v1', embedding_model='mock', content_hash='hash'))
    isolated_db.flush()
    isolated_db.add(ChunkMember(chunk_id='CK-KEEP', knowledge_id='KEEP', position=1))
    isolated_db.flush()
    with pytest.raises(ValueError):
        import_excel.import_knowledge(isolated_db, path, load_mapping(MAPPING_PATH), gate=True)
    assert isolated_db.get(KnowledgeItem, 'KEEP').text == 'Keep me'
    assert isolated_db.get(KnowledgeItem, 'K1') is None
    assert isolated_db.get(Chunk, 'CK-KEEP').chunk_text == 'Keep chunk'


def test_unsafe_video_import_is_rejected_without_optional_gate(tmp_path, isolated_db):
    path = tmp_path / 'unsafe.xlsx'
    write_workbook(path, [claim(author_stance='School A', release_status='LOCKED')],
                   [{**SOURCES[0], 'source_type': 'VIDEO'}])
    with pytest.raises(ValueError, match='source_d_'):
        import_excel.import_knowledge(isolated_db, path, load_mapping(MAPPING_PATH))
    assert isolated_db.get(KnowledgeItem, 'K1') is None


def test_gate_allows_unpaged_school_record_to_be_stored_without_evidence(tmp_path, isolated_db):
    path = tmp_path / 'school.xlsx'
    write_workbook(path, [claim(author_stance='School A')])
    stats = import_excel.import_knowledge(isolated_db, path, load_mapping(MAPPING_PATH), gate=True)
    isolated_db.flush()
    assert stats['imported'] == 1
    assert isolated_db.get(KnowledgeItem, 'K1').evidences == []


def test_video_source_cannot_replace_existing_book_identity(tmp_path, isolated_db):
    isolated_db.add(Book(book_code='NPL', source_id='CANONICAL', title='Existing canonical book'))
    isolated_db.flush()
    path = tmp_path / 'video.xlsx'
    write_workbook(path, [claim(author_stance='School A', release_status='DRAFT_NOT_RELEASED',
                                review_flag='HYPOTHESIS_NEEDS_VALIDATION')],
                   [{**SOURCES[0], 'source_type': 'VIDEO', 'title': 'Video title'}])
    import_excel.import_books(isolated_db, path, load_mapping(MAPPING_PATH))
    book = isolated_db.get(Book, 'NPL')
    assert book.source_id == 'CANONICAL'
    assert book.title == 'Existing canonical book'
