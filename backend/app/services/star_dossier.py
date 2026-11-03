"""T6: source-separated dossiers; deterministic lookup, never LLM knowledge creation."""
from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import yaml

from backend.app.core.config import DB_PATH, ROOT
from backend.app.services.horoscope_rag_bridge import STAR_NAMES, normalized, search_fts_sqlite
from backend.app.services.knowledge_gate import validate_records

SLOTS = {
    'core_function': 'Bản chất và ý nghĩa biểu tượng',
    'yin_yang_five_element': 'Âm dương và ngũ hành',
    'favorable_expression': 'Biểu hiện thuận', 'unfavorable_expression': 'Biểu hiện cần cân nhắc',
    'strength_by_branch': 'Miếu, vượng, đắc, hãm', 'by_palace': 'Theo cung',
    'supportive_combinations': 'Tổ hợp hỗ trợ', 'challenging_combinations': 'Tổ hợp cần đối chiếu',
    'transformation_behavior': 'Tứ Hóa', 'with_tuan_triet': 'Khi gặp Tuần, Triệt',
    'with_sat_tinh': 'Khi gặp sát tinh', 'school_differences': 'Tiếng nói từng sách và trường phái',
    'case_notes': 'Ca nghiệm lý', 'source_citations': 'Trích dẫn sách',
}
MISSING = 'chưa có trong kho tri thức hiện tại'
SEED_MESSAGE = 'Tham khảo, chưa đối chiếu sách KMS'
SEED_STARS = ('Tử Vi','Thiên Cơ','Thái Dương','Vũ Khúc','Thiên Đồng','Liêm Trinh','Thiên Phủ',
              'Thái Âm','Tham Lang','Cự Môn','Thiên Tướng','Thiên Lương','Thất Sát','Phá Quân',
              'Tả Phụ','Hữu Bật','Văn Xương','Văn Khúc','Thiên Khôi','Thiên Việt')
KNOWN_STARS = {normalized(name): name.title() for name in STAR_NAMES.values()}
KNOWN_STARS.update({normalized(name): name for name in SEED_STARS})
SEED_PATH = ROOT/'configs/star_seeds'


class UnknownStar(ValueError):
    pass


def canonical_star(name: str) -> str:
    key = normalized(name)
    if key not in KNOWN_STARS:
        raise UnknownStar('Tên sao không hợp lệ.')
    return KNOWN_STARS[key]


def load_star_seed(name: str) -> dict:
    name = canonical_star(name)
    path = SEED_PATH/(normalized(name).replace(' ','_')+'.yaml')
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('name') != name or not isinstance(data.get('slots'), dict):
        raise ValueError(f'Invalid star seed: {path.name}')
    records = []
    for slot, entry in data['slots'].items():
        if (slot not in SLOTS or slot in {'case_notes','source_citations'} or not isinstance(entry, dict)
                or entry.get('status') != 'seed_unverified' or not entry.get('source') or not entry.get('reference')):
            raise ValueError(f'Invalid seed slot: {path.name}:{slot}')
        records.append({'knowledge_id':f'SEED-{normalized(name)}-{slot}', 'text':entry.get('text'),
                        'source_id':'REPO2', 'author_stance':'Biên soạn gián tiếp của repo hung-ngm, chưa xác minh',
                        'release_status':'DRAFT_NOT_RELEASED'})
    validate_records(records, [{'source_id':'REPO2','source_type':'BOOK','title':data.get('source')}]).require_valid()
    return data['slots']


def _mentions(name: str, value: str) -> bool:
    return f' {normalized(name)} ' in f' {normalized(value or "")} '


def _records(name: str, path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True) as conn:
        conn.row_factory = sqlite3.Row
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
        fts_ids = set()
        if {'chunks_fts','chunk_members','chunks'} <= tables:
            for book in ('NPL','BD','DAU'):
                hits = search_fts_sqlite(name, limit=30, book_code=book, db_path=path)
                for hit in hits:
                    fts_ids.update(r[0] for r in conn.execute('SELECT knowledge_id FROM chunk_members WHERE chunk_id=?',(hit['chunk_id'],)))
        columns = {r[1] for r in conn.execute('PRAGMA table_info(knowledge_items)')}
        stance = 'author_stance' if 'author_stance' in columns else 'NULL AS author_stance'
        rows = conn.execute(f'''SELECT knowledge_id, book_code, subject, predicate, taxonomy_code,
                text, condition_context, trust_tier, review_flag, conflict_status, {stance}
                FROM knowledge_items WHERE trust_tier IN (1,2,3)
                AND book_code IN ('NPL','BD','DAU') ORDER BY book_code,knowledge_id''').fetchall()
        found = []
        for row in rows:
            if 'HYPOTHESIS_NEEDS_VALIDATION' in (row['review_flag'] or '').upper():
                continue
            subject = row['subject'] or ''
            matched = _mentions(name, subject) or _mentions(name, (row['taxonomy_code'] or '').replace('_',' '))
            matched = matched or (row['knowledge_id'] in fts_ids and _mentions(name, row['text']))
            if normalized(name) == 'tu vi':
                matched = matched and (normalized(subject).startswith('tu vi') or _mentions('sao Tử Vi',row['text']))
            if not matched:
                continue
            citations = []
            if 'knowledge_pages' in tables:
                citations = [{'book_code':row['book_code'],'part_number':p[0],'pdf_page':p[1]}
                             for p in conn.execute('SELECT part_number,pdf_page FROM knowledge_pages WHERE knowledge_id=? AND pdf_page>0',(row['knowledge_id'],))]
            if not citations and 'evidences' in tables:
                citations = [{'book_code':row['book_code'],'part_number':p[0],'pdf_page':p[1]}
                             for p in conn.execute('SELECT part_number,pdf_page FROM evidences WHERE knowledge_id=? AND pdf_page>0',(row['knowledge_id'],))]
            if not citations:
                continue
            entry = dict(row)
            entry.update(source_type='canonical', status='unverified', citations=citations)
            found.append(entry)
        # Balanced sources: one prolific OCR book must not suppress the other voices.
        return [r for book in ('NPL','BD','DAU') for r in [x for x in found if x['book_code']==book][:30]]


def _slot_keys(record: dict) -> set[str]:
    label = normalized(' '.join(str(record.get(k) or '') for k in ('subject','predicate','taxonomy_code','condition_context')))
    keys = set()
    relation = str(record.get('predicate') or '').upper()
    relation_slots = {'MEANS':'core_function', 'DEFINES':'core_function', 'HAS_PROPERTY':'core_function',
                      'STRENGTHENS':'supportive_combinations','AMPLIFIES':'supportive_combinations',
                      'WEAKENS':'challenging_combinations','TRANSFORMS':'transformation_behavior'}
    if relation in relation_slots:
        keys.add(relation_slots[relation])
    patterns = {
        'core_function': ('ban chat','dinh nghia','y nghia','chuc nang'),
        'yin_yang_five_element': ('ngu hanh','am duong'),
        'favorable_expression': ('thuan','tot','cat loi'),
        'unfavorable_expression': ('nghich','xau','bat loi'),
        'strength_by_branch': ('mieu','vuong','dac dia','ham'),
        'by_palace': ('cung','ngo','menh','tai bach','quan loc','phu the'),
        'supportive_combinations': ('ho tro','cat tinh'),
        'challenging_combinations': ('bat loi','to hop xau'),
        'transformation_behavior': ('hoa loc','hoa quyen','hoa khoa','hoa ky','tu hoa'),
        'with_tuan_triet': ('tuan','triet'), 'with_sat_tinh': ('sat tinh','kinh duong','da la','hoa linh','khong kiep'),
    }
    for slot, terms in patterns.items():
        if any(f' {term} ' in f' {label} ' for term in terms):
            keys.add(slot)
    # Unclassified source material stays in the per-book view; never invent a slot assignment.
    return keys | {'school_differences'}


def get_star_dossier(name: str, *, db_path: Path | str | None = None, include_seeds: bool = False) -> dict:
    name = canonical_star(name)
    slots = {key:{'label':label,'status':'missing','message':MISSING,'entries':[]} for key,label in SLOTS.items()}
    records = _records(name, Path(db_path or DB_PATH))
    for record in records:
        for key in _slot_keys(record):
            slots[key]['entries'].append(record)
        slots['source_citations']['entries'].append({'knowledge_id':record['knowledge_id'],
            'book_code':record['book_code'],'citations':record['citations'],'status':'unverified'})
    for slot in slots.values():
        if slot['entries']:
            slot.update(status='canonical',message='Nguồn KMS; giữ riêng từng sách, chưa kiểm duyệt thủ công.')
    enabled = os.getenv('KMS_STAR_SEEDS_ENABLED','1').strip().lower() in {'1','true','yes'}
    if include_seeds and enabled:
        for key, entry in load_star_seed(name).items():
            if not slots[key]['entries']:
                slots[key].update(status='seed_unverified',message=SEED_MESSAGE,entries=[dict(entry)])
    return {'name':name, 'slots':slots,'canonical_records':len(records),
            'books':[b for b in ('NPL','DAU','BD') if any(r['book_code']==b for r in records)], 'seed_enabled':bool(include_seeds and enabled),
            'tin_cay':[{'book_code':b, 'trust_tiers':sorted({r['trust_tier'] for r in records if r['book_code']==b}),
                        'label':'Đối chiếu theo nguồn; chưa xác minh toàn bộ điều kiện hoặc trang thủ công.'}
                       for b in sorted({r['book_code'] for r in records})]}
