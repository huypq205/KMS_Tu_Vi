"""P2 (Plan_Fix_Mai_Anh_v2): danh mục quy tắc cách cục đã kiểm kê từ nguồn tham khảo.

Nguồn: ``skills/tu-vi-dau-so-main/.../references/cach_cuc_luan_giai.md``
(tham khảo, chưa đối chiếu KMS — nhãn ``source_status: reference_unverified``,
giống quy ước của ``star_meanings_reference``).

Trách nhiệm (P2 §4.2): danh mục do AI/engineer kiểm kê, chuẩn hóa và viết test;
``duyet_dung`` chỉ được gán khi có người duyệt chuyên môn được chỉ định tại
``reviewer_role`` — không ai tự duyệt. Khi ``reviewer_role == 'chua_chi_dinh'``,
mọi rule ở trạng thái khác ``duyet_dung``.

Trạng thái (P2 §4.1/§4.3)
--------------------------
- ``duyet_dung``: được phép dùng trong sản phẩm (cần người duyệt + mốc duyệt).
- ``chi_tham_khao``: chỉ tham khảo, chưa xác minh nội dung.
- ``can_doi_chieu``: có điểm mơ hồ/mâu thuẫn hoặc nội dung nhạy cảm cần đối chiếu.
- ``chua_ho_tro``: engine chưa đáp ứng dữ kiện, chưa tự động hóa được.

``san_sang_thuc_thi`` (chân thẳng góc với trạng thái nội dung): điều kiện đã đủ
rõ để bộ nhận diện (P3) thực thi — không còn điểm mơ hồ, đủ 3 ca kiểm thử.
``ung_vien_ban_dau``: tập con (<=8) đưa vào bản đầu của P3.

Trường máy đọc bổ sung cho P3: ``trang_thai_sao`` (mapping tên sao -> một
trong ``mieu/vuong/dac/binh/ham``) cho quy tắc yêu cầu trạng thái sao. Đây là
khai báo điều kiện của quy tắc, **không** phải bảng miếu vượng mới.

File: ``configs/cach_cuc_catalog.yaml``.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from backend.app.core.config import ROOT
from backend.app.services.tu_hoa_tables import normalize_star

CACH_CUC_CATALOG_PATH = ROOT / 'configs' / 'cach_cuc_catalog.yaml'

RULE_STATUSES = ('duyet_dung', 'chi_tham_khao', 'can_doi_chieu', 'chua_ho_tro')
RULE_GROUPS = ('quy_cach', 'pha_cach')
RELATIONSHIPS = ('dong_cung', 'tam_hop', 'xung_chieu', 'giap_cung')
TIME_LAYERS = ('la_so_goc', 'dai_han', 'luu_nien')
CAN_STEMS = ('Giáp', 'Ất', 'Bính', 'Đinh', 'Mậu', 'Kỷ', 'Canh', 'Tân', 'Nhâm', 'Quý')
CHI_BRANCHES = ('Tý', 'Sửu', 'Dần', 'Mão', 'Thìn', 'Tỵ', 'Ngọ', 'Mùi',
                'Thân', 'Dậu', 'Tuất', 'Hợi')
DAC_TINH_STATES = ('mieu', 'vuong', 'dac', 'binh', 'ham')
REVIEWER_UNSET = 'chua_chi_dinh'
MAX_BATCH_CANDIDATES = 8


class CatalogError(ValueError):
    """Danh mục cách cục sai schema hoặc vi phạm bất biến (P2 §4.3/§4.6)."""


REQUIRED_RULE_FIELDS = (
    'id', 'ten', 'nhom', 'sao', 'dieu_kien', 'quan_he', 'chi', 'can_tuoi',
    'tang_thoi_gian', 'diem_mo_ho', 'noi_dung_nhay_cam', 'ca_kiem_thu',
    'diem_giai_trinh', 'san_sang_thuc_thi', 'ung_vien_ban_dau',
    'trang_thai', 'nguoi_duyet', 'ngay_duyet',
)
CA_KEYS = ('duong', 'am', 'thieu')


def _normalize_rule(rule: dict, index: int) -> dict:
    """Chuẩn hóa giá trị mặc định; raise CatalogError khi thiếu trường bắt buộc."""
    if not isinstance(rule, dict):
        raise CatalogError(f'rule #{index}: không phải mapping.')
    for field in REQUIRED_RULE_FIELDS:
        if field not in rule:
            raise CatalogError(f'rule #{index} ({rule.get("id", "?")}): thiếu trường "{field}".')
    normalized = dict(rule)
    normalized.setdefault('cung_neo', None)
    normalized.setdefault('cung_muc_tieu', [])
    normalized.setdefault('trang_thai_sao', {})
    normalized.setdefault('noi_dung_da_duyet', False)
    return normalized


def _validate(catalog: dict) -> None:
    if not isinstance(catalog, dict) or catalog.get('version') != 1:
        raise CatalogError('version phải bằng 1.')
    source_file = catalog.get('source_file')
    if not isinstance(source_file, str) or not source_file.strip():
        raise CatalogError('source_file bắt buộc (đường dẫn tương đối từ ROOT).')
    # File nguồn thiếu phải được nhận diện đúng, không chạy im lặng (P2 §4.6).
    if not (ROOT / source_file).is_file():
        raise CatalogError(f'File nguồn không tồn tại: {source_file} (dựa trên ROOT).')
    reviewer_role = catalog.get('reviewer_role')
    if not isinstance(reviewer_role, str) or not reviewer_role.strip():
        raise CatalogError('reviewer_role bắt buộc (hoặc "%s" khi chưa chỉ định).' % REVIEWER_UNSET)
    if not isinstance(catalog.get('source_status'), str) or not catalog['source_status'].strip():
        raise CatalogError('source_status bắt buộc.')

    rules = catalog.get('rules')
    if not isinstance(rules, list) or not rules:
        raise CatalogError('rules phải là danh sách khác rỗng.')
    seen_ids: set[str] = set()
    normalized_rules = []
    for index, rule in enumerate(rules):
        normalized = _normalize_rule(rule, index)
        rid = normalized['id']
        if not isinstance(rid, str) or not rid.strip():
            raise CatalogError(f'rule #{index}: id không hợp lệ.')
        if rid in seen_ids:
            raise CatalogError(f'rule "{rid}": id trùng trong danh mục.')
        seen_ids.add(rid)
        if normalized['nhom'] not in RULE_GROUPS:
            raise CatalogError(f'rule "{rid}": nhom phải thuộc {RULE_GROUPS}.')
        if normalized['trang_thai'] not in RULE_STATUSES:
            raise CatalogError(f'rule "{rid}": trang_thai không hợp lệ '
                               f'(được phép: {", ".join(RULE_STATUSES)}).')
        if not isinstance(normalized['sao'], list):
            raise CatalogError(f'rule "{rid}": sao phải là danh sách ([] nếu quy tắc không dựa trên sao).')
        # P3: điều kiện trạng thái sao phải máy đọc được, không suy từ văn bản.
        trang_thai_sao = normalized['trang_thai_sao']
        if not isinstance(trang_thai_sao, dict):
            raise CatalogError(f'rule "{rid}": trang_thai_sao phải là mapping tên sao -> trạng thái.')
        rule_stars = {normalize_star(name) for name in normalized['sao'] if isinstance(name, str)}
        for star_name, state in trang_thai_sao.items():
            if not isinstance(star_name, str) or not star_name.strip():
                raise CatalogError(f'rule "{rid}": trang_thai_sao có tên sao không hợp lệ.')
            if normalize_star(star_name) not in rule_stars:
                raise CatalogError(f'rule "{rid}": trang_thai_sao nêu sao "{star_name}" '
                                   'không thuộc danh sách sao của quy tắc.')
            if state not in DAC_TINH_STATES:
                raise CatalogError(f'rule "{rid}": trạng thái sao "{state}" không hợp lệ '
                                   f'(được phép: {", ".join(DAC_TINH_STATES)}).')
        dieu_kien = normalized['dieu_kien']
        if (not isinstance(dieu_kien, dict)
                or not isinstance(dieu_kien.get('bat_buoc'), list) or not dieu_kien['bat_buoc']):
            raise CatalogError(f'rule "{rid}": dieu_kien.bat_buoc phải là danh sách khác rỗng.')
        for list_key in ('ho_tro', 'pha_cach'):
            if not isinstance(dieu_kien.get(list_key, []), list):
                raise CatalogError(f'rule "{rid}": dieu_kien.{list_key} phải là danh sách.')
        for rel in normalized['quan_he']:
            if rel not in RELATIONSHIPS:
                raise CatalogError(f'rule "{rid}": quan hệ "{rel}" không thuộc {RELATIONSHIPS}.')
        for branch in normalized['chi']:
            if branch not in CHI_BRANCHES:
                raise CatalogError(f'rule "{rid}": chi "{branch}" không hợp lệ.')
        for stem in normalized['can_tuoi']:
            if stem not in CAN_STEMS:
                raise CatalogError(f'rule "{rid}": can tuổi "{stem}" không hợp lệ.')
        # Trạng thái boolean phải đúng kiểu (YAML "false" dạng string không được ngầm coi là dùng).
        for flag in ('san_sang_thuc_thi', 'noi_dung_nhay_cam', 'ung_vien_ban_dau', 'noi_dung_da_duyet'):
            if not isinstance(normalized[flag], bool):
                raise CatalogError(f'rule "{rid}": {flag} phải là true/false, nhận {normalized[flag]!r}.')
        if not isinstance(normalized['diem_mo_ho'], list):
            raise CatalogError(f'rule "{rid}": diem_mo_ho phải là danh sách.')
        if normalized['tang_thoi_gian'] not in TIME_LAYERS:
            raise CatalogError(f'rule "{rid}": tang_thoi_gian phải thuộc {TIME_LAYERS}.')
        ca = normalized['ca_kiem_thu']
        if (not isinstance(ca, dict)
                or any(not isinstance(ca.get(key), str) for key in CA_KEYS)):
            raise CatalogError(f'rule "{rid}": ca_kiem_thu phải có duong/am/thieu (string).')
        # I1: sẵn sàng thực thi <=> không còn điểm mơ hồ + đủ 3 ca (P2 §4.3).
        if normalized['san_sang_thuc_thi']:
            if normalized['diem_mo_ho'] != []:
                raise CatalogError(f'rule "{rid}": san_sang_thuc_thi nhưng còn diem_mo_ho.')
            if not all(ca[key].strip() for key in CA_KEYS):
                raise CatalogError(f'rule "{rid}": san_sang_thuc_thi nhưng thiếu ca kiểm thử.')
        # I2: duyet_dung chỉ khi có người duyệt + mốc; reviewer chưa chỉ định thì cấm.
        if normalized['trang_thai'] == 'duyet_dung':
            if reviewer_role == REVIEWER_UNSET:
                raise CatalogError(f'rule "{rid}": duyet_dung không được phép khi '
                                   f'reviewer_role="{REVIEWER_UNSET}" (P2 §4.2).')
            if not (normalized.get('nguoi_duyet') and normalized.get('ngay_duyet')):
                raise CatalogError(f'rule "{rid}": duyet_dung yêu cầu nguoi_duyet và ngay_duyet.')
        # I3: nội dung nhạy cảm chưa duyệt không vào trạng thái "được dùng" (P2 §4.5).
        if (normalized['noi_dung_nhay_cam'] and not normalized.get('noi_dung_da_duyet')
                and normalized['trang_thai'] not in ('chi_tham_khao', 'can_doi_chieu')):
            raise CatalogError(f'rule "{rid}": nội dung nhạy cảm chưa duyệt nội dung '
                               f'chỉ được ở chi_tham_khao/can_doi_chieu.')
        # I4: ứng viên bản đầu phải đủ rõ và không nhạy cảm.
        if normalized['ung_vien_ban_dau']:
            if not normalized['san_sang_thuc_thi']:
                raise CatalogError(f'rule "{rid}": ung_vien_ban_dau yêu cầu san_sang_thuc_thi.')
            if normalized['noi_dung_nhay_cam']:
                raise CatalogError(f'rule "{rid}": ứng viên bản đầu không được có nội dung nhạy cảm.')
        normalized_rules.append(normalized)
    # I5: bản đầu giới hạn số lượng (P2: "khoảng 5-8 cách cục").
    if sum(r['ung_vien_ban_dau'] for r in normalized_rules) > MAX_BATCH_CANDIDATES:
        raise CatalogError(f'Số ứng viên bản đầu vượt tối đa {MAX_BATCH_CANDIDATES}.')

    sections = catalog.get('sections_khong_phan_van', [])
    if not isinstance(sections, list):
        raise CatalogError('sections_khong_phan_van phải là danh sách.')
    for section in sections:
        if (not isinstance(section, dict) or not isinstance(section.get('ma'), int)
                or not section.get('ten') or not section.get('ly_do')):
            raise CatalogError('Mỗi section cần ma (int), ten và ly_do.')
        section.setdefault('noi_dung_nhay_cam', False)
        section.setdefault('ghi_chu', '')
    catalog['rules'] = normalized_rules
    catalog['sections_khong_phan_van'] = sections


def load_catalog(path: Path | None = None) -> dict:
    """Tải và validate danh mục cách cục. Trả về catalog đã chuẩn hóa (không sửa file)."""
    catalog_path = Path(path) if path is not None else CACH_CUC_CATALOG_PATH
    try:
        raw = yaml.safe_load(catalog_path.read_text(encoding='utf-8'))
    except (OSError, yaml.YAMLError) as exc:
        raise CatalogError(f'Không đọc được danh mục cách cục {catalog_path}: {exc}') from exc
    if not isinstance(raw, dict):
        raise CatalogError('Danh mục cách cục phải là YAML mapping.')
    _validate(raw)
    return raw


def get_rule(catalog: dict, rule_id: str) -> dict:
    """Lấy rule theo id; raise KeyError nếu không tồn tại."""
    for rule in catalog['rules']:
        if rule['id'] == rule_id:
            return rule
    raise KeyError(f'Quy tắc không tồn tại trong danh mục: {rule_id}')


def filter_rules(catalog: dict, nhom: str | None = None, trang_thai: str | None = None,
                 san_sang_thuc_thi: bool | None = None, noi_dung_nhay_cam: bool | None = None,
                 ung_vien_ban_dau: bool | None = None) -> list[dict]:
    """Lọc danh mục theo tiêu chí (P3 dùng để lấy tập quy tắc cần nhận diện)."""
    result = []
    for rule in catalog['rules']:
        if nhom is not None and rule['nhom'] != nhom:
            continue
        if trang_thai is not None and rule['trang_thai'] != trang_thai:
            continue
        if san_sang_thuc_thi is not None and rule['san_sang_thuc_thi'] != san_sang_thuc_thi:
            continue
        if noi_dung_nhay_cam is not None and rule['noi_dung_nhay_cam'] != noi_dung_nhay_cam:
            continue
        if ung_vien_ban_dau is not None and rule['ung_vien_ban_dau'] != ung_vien_ban_dau:
            continue
        result.append(rule)
    return result


def batch_candidates(catalog: dict) -> list[dict]:
    """Các quy tắc P3 nhận diện trong bản đầu (<=8, đủ rõ, không nhạy cảm)."""
    return filter_rules(catalog, ung_vien_ban_dau=True)


def catalog_signature(catalog: dict) -> str:
    """Dấu vân tay nội dung danh mục — dùng cho cache (P6) và truy ngược nguồn (P2 §v1)."""
    blob = json.dumps(
        {'version': catalog.get('version'), 'source_file': catalog.get('source_file'),
         'rules': catalog.get('rules')},
        sort_keys=True, ensure_ascii=False,
    )
    return hashlib.sha256(blob.encode('utf-8')).hexdigest()
