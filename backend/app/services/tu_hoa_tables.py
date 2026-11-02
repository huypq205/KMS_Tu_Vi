"""T5: explicit, separately attributed Tứ Hóa tables. No vendor mutation."""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import unicodedata

import yaml

from backend.app.core.config import ROOT

CONFIG_PATH = ROOT / 'configs' / 'tu_hoa_tables.yaml'
STEMS = ('Giáp', 'Ất', 'Bính', 'Đinh', 'Mậu', 'Kỷ', 'Canh', 'Tân', 'Nhâm', 'Quý')
TU_HOA_CODES = ('HOA_LOC', 'HOA_QUYEN', 'HOA_KHOA', 'HOA_KY')
TU_HOA_STAR_IDS = {'HOA_LOC': 94, 'HOA_QUYEN': 93, 'HOA_KHOA': 92, 'HOA_KY': 95}
PARENT_STARS = (
    'Tử Vi', 'Liêm Trinh', 'Thiên Đồng', 'Vũ Khúc', 'Thái Dương', 'Thiên Cơ',
    'Thiên Phủ', 'Thái Âm', 'Tham Lang', 'Cự Môn', 'Thiên Tướng', 'Thiên Lương',
    'Thất Sát', 'Phá Quân', 'Văn Xương', 'Văn Khúc', 'Tả Phụ', 'Hữu Bật',
)


def normalize_star(name: str) -> str:
    result = ''.join(c for c in unicodedata.normalize('NFD', name.casefold())
                     if unicodedata.category(c) != 'Mn').replace('đ', 'd')
    return result.strip()


def load_tu_hoa_config(path: Path = CONFIG_PATH) -> dict:
    raw = yaml.safe_load(Path(path).read_text(encoding='utf-8'))
    if not isinstance(raw, dict) or raw.get('version') != 1 or not isinstance(raw.get('tables'), dict):
        raise ValueError('Invalid Tứ Hóa configuration schema.')
    if not raw['tables'] or raw.get('default_table') not in raw['tables']:
        raise ValueError('Invalid default Tứ Hóa table.')
    valid_stars = {normalize_star(name) for name in PARENT_STARS}
    result = {'default_table': raw['default_table'], 'tables': {}}
    for table_id, table in raw['tables'].items():
        if not isinstance(table_id, str) or not isinstance(table, dict):
            raise ValueError('Invalid Tứ Hóa table.')
        for key in ('school', 'source', 'verification_status'):
            if not isinstance(table.get(key), str) or not table[key].strip():
                raise ValueError(f'Table {table_id}: missing {key}.')
        rows = table.get('by_can')
        if not isinstance(rows, dict) or set(rows) != set(STEMS):
            raise ValueError(f'Table {table_id} must contain exactly ten stems.')
        by_can = {}
        for can, values in rows.items():
            if (not isinstance(values, list) or len(values) != 4
                    or not all(isinstance(name, str) and normalize_star(name) in valid_stars for name in values)
                    or len({normalize_star(name) for name in values}) != 4):
                raise ValueError(f'Table {table_id}, {can}: expected four valid distinct parent stars.')
            by_can[can] = dict(zip(TU_HOA_CODES, values))
        entry = {key: table[key] for key in ('school', 'source', 'verification_status')}
        entry.update(id=table_id, by_can=by_can)
        entry['signature'] = hashlib.sha256(json.dumps(entry, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
        result['tables'][table_id] = entry
    return result


@lru_cache(maxsize=4)
def _cached_config(path: Path, modified_ns: int) -> dict:
    return load_tu_hoa_config(path)


def get_tu_hoa_table(table_id: str | None = None) -> dict:
    config = _cached_config(CONFIG_PATH, CONFIG_PATH.stat().st_mtime_ns)
    selected = table_id if table_id is not None else os.getenv('KMS_TU_HOA_TABLE', '').strip() or config['default_table']
    if selected not in config['tables']:
        raise ValueError(f'Unknown Tứ Hóa table: {selected}')
    return deepcopy(config['tables'][selected])


def table_metadata(table: dict) -> dict:
    return {key: table[key] for key in ('id', 'school', 'source', 'verification_status', 'signature')}


def find_parent_palace(palaces: list[dict], star_name: str) -> dict | None:
    target = normalize_star(star_name)
    return next((p for p in palaces
                 if any(normalize_star(s.get('saoTen', '')) == target for s in p.get('saos', []))), None)


def apply_natal_table(palaces: list[dict], can: str, table: dict) -> None:
    """Move only differing hóa tinh in the adapter's owned chart dictionaries.

    Default placement and order are preserved. Dignity is recomputed on a copied
    Sao object for a moved star; global catalog and vendor source stay untouched.
    """
    from lasotuvi import Sao as catalog
    from lasotuvi.DiaBan import dacTinhSao

    specs = {94: catalog.saoHoaLoc, 93: catalog.saoHoaQuyen,
             92: catalog.saoHoaKhoa, 95: catalog.saoHoaKy}
    # Validate all parents before changing any placement.
    targets = {code: find_parent_palace(palaces, parent) for code, parent in table['by_can'][can].items()}
    if any(p is None for p in targets.values()):
        raise ValueError(f'Missing Tứ Hóa parent star for {can}, table {table["id"]}.')
    for code, target in targets.items():
        sid = TU_HOA_STAR_IDS[code]
        matches = [(p, s) for p in palaces for s in p['saos'] if s['saoID'] == sid]
        if len(matches) != 1:
            raise ValueError(f'Expected exactly one hóa tinh {sid}.')
        current, star = matches[0]
        if current is target:
            continue
        updated = deepcopy(specs[sid])
        updated.saoDacTinh = None
        dacTinhSao(target['cung_so'], updated)
        current['saos'].remove(star)
        target['saos'].append(updated.__dict__.copy())
