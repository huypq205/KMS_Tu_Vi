"""P2 (Plan_Fix_Mai_Anh_v2): kiểm kê và duyệt nguồn cách cục.

- Danh mục 30 quy tắc (21 quý cách + 9 phá cách) từ
  skills/.../references/cach_cuc_luan_giai.md (nguồn tham khảo, chưa đối chiếu KMS).
- Trạng thái nguồn (4 giá trị) + trạng thái sẵn sàng thực thi (chân thẳng góc, P2 §4.1).
- Không tự duyệt (P2 §4.2): khi catalog khai reviewer_role='chua_chi_dinh',
  không rule nào được 'duyet_dung'; 'duyet_dung' luôn yêu cầu nguoi_duyet + ngay_duyet.
- Nội dung nhạy cảm (tử vong/tuổi thọ/phẩm hạnh/giới) không được 'duyet_dung'
  khi chưa có duyệt nội dung (P2 §4.5).
- P3 chỉ nhận các quy tắc 'ung_vien_ban_dau' (≤8, đủ rõ, không nhạy cảm).
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from backend.app.services.cach_cuc_catalog import (
    CatalogError,
    batch_candidates,
    catalog_signature,
    filter_rules,
    get_rule,
    load_catalog,
)


def _dump(catalog: dict) -> str:
    return yaml.safe_dump(catalog, allow_unicode=True, sort_keys=False)


# --- P2.TC-01: danh mục đủ 30 quy tắc, id duy nhất, chưa có quy tắc nào duyet_dung ---
def test_catalog_loads_30_rules_with_unique_ids():
    catalog = load_catalog()
    rules = catalog["rules"]
    assert len(rules) == 30
    nhom: dict[str, int] = {}
    for rule in rules:
        nhom[rule["nhom"]] = nhom.get(rule["nhom"], 0) + 1
    assert nhom == {"quy_cach": 21, "pha_cach": 9}
    ids = [rule["id"] for rule in rules]
    assert len(set(ids)) == 30
    # Chưa chỉ định người duyệt chuyên môn: không rule nào duyet_dung, nguoi_duyet đều null.
    assert catalog["reviewer_role"] == "chua_chi_dinh"
    assert all(rule["trang_thai"] != "duyet_dung" for rule in rules)
    assert all(rule["nguoi_duyet"] is None for rule in rules)


# --- P2.TC-02: trạng thái hợp lệ; nội dung nhạy cảm chưa được dùng trong sản phẩm ---
def test_statuses_valid_and_sensitive_rules_blocked():
    catalog = load_catalog()
    for rule in catalog["rules"]:
        assert rule["trang_thai"] in ("duyet_dung", "chi_tham_khao", "can_doi_chieu", "chua_ho_tro")
        if rule["noi_dung_nhay_cam"]:
            # Chưa có người duyệt -> nhạy cảm tối đa chỉ được ở tham khảo/đối chiếu.
            assert rule["trang_thai"] in ("chi_tham_khao", "can_doi_chieu"), rule["id"]
            assert rule["nguoi_duyet"] is None, rule["id"]
    # Các quy tắc luận về tử vong trong nguồn phải được gắn nhãn nhạy cảm.
    sensitive_ids = {r["id"] for r in catalog["rules"] if r["noi_dung_nhay_cam"]}
    assert {"pha-linh-xuong-da-vu", "pha-cu-hoa-kinh-duong",
            "pha-ma-dau-dai-kiem", "pha-menh-vu-chinh-dieu"} <= sensitive_ids


# --- P2.TC-03: sẵn sàng thực thi <=> không còn điểm mơ hồ + đủ 3 ca kiểm thử ---
def test_execution_ready_invariant():
    catalog = load_catalog()
    for rule in catalog["rules"]:
        if rule["san_sang_thuc_thi"]:
            assert rule["diem_mo_ho"] == [], rule["id"]
            ca = rule["ca_kiem_thu"]
            assert ca["duong"].strip() and ca["am"].strip() and ca["thieu"].strip(), rule["id"]


# --- P2.TC-04: đúng 8 ứng viên bản đầu, đủ rõ và không nhạy cảm ---
def test_batch_candidates_are_exactly_eight_and_safe():
    catalog = load_catalog()
    batch = batch_candidates(catalog)
    assert len(batch) == 8
    for rule in batch:
        assert rule["san_sang_thuc_thi"] is True
        assert rule["noi_dung_nhay_cam"] is False
        assert rule["trang_thai"] in ("chi_tham_khao", "duyet_dung")


# --- P2.TC-05: các section không phải cách cục (3–10) được khai báo, không âm thầm ---
def test_out_of_scope_sections_are_declared():
    catalog = load_catalog()
    sections = {s["ma"]: s for s in catalog["sections_khong_phan_van"]}
    # Thất Hãm (yểu chiết) và Nam Nữ Mệnh (phẩm hạnh/giới) bắt buộc có nhãn nhạy cảm.
    assert sections[4]["noi_dung_nhay_cam"] is True
    assert sections[8]["noi_dung_nhay_cam"] is True
    for section in catalog["sections_khong_phan_van"]:
        assert section["ten"].strip() and section["ly_do"].strip()
    # Không rule nào trùng tên section (các section này không nằm trong danh mục).
    rule_heads = {r["ten"] for r in catalog["rules"]}
    assert not (rule_heads & {s["ten"] for s in catalog["sections_khong_phan_van"]})


# --- P2.TC-06: lọc danh mục theo tiêu chí (P3 dùng filter + batch) ---
def test_filter_rules():
    catalog = load_catalog()
    assert all(r["nhom"] == "pha_cach" for r in filter_rules(catalog, nhom="pha_cach"))
    assert all(r["trang_thai"] == "can_doi_chieu"
               for r in filter_rules(catalog, trang_thai="can_doi_chieu"))
    no_ready = filter_rules(catalog, san_sang_thuc_thi=False)
    assert no_ready and all(not r["san_sang_thuc_thi"] for r in no_ready)
    assert get_rule(catalog, "quy-tu-pu-dong-cung")["ten"] == "Tử Phủ đồng cung"
    with pytest.raises(KeyError):
        get_rule(catalog, "khong-ton-tai")


# --- P2.TC-07: signature ổn định khi tải lặp, đổi khi nội dung đổi ---
def test_catalog_signature_stable_and_content_bound():
    assert catalog_signature(load_catalog()) == catalog_signature(load_catalog())
    catalog = load_catalog()
    catalog["rules"][0]["trang_thai"] = "chua_ho_tro"
    assert catalog_signature(catalog) != catalog_signature(load_catalog())


# --- P2.TC-08: validator bắt sai trạng thái, trùng id, tự duyệt, nguồn thiếu ---
def test_rejects_invalid_status(tmp_path: Path):
    catalog = load_catalog()
    catalog["rules"][0]["trang_thai"] = "trang_thai_lai"
    path = tmp_path / "bad_status.yaml"
    path.write_text(_dump(catalog), encoding="utf-8")
    with pytest.raises(CatalogError):
        load_catalog(path)


def test_rejects_duplicate_rule_id(tmp_path: Path):
    catalog = load_catalog()
    catalog["rules"][1]["id"] = catalog["rules"][0]["id"]
    path = tmp_path / "dup_id.yaml"
    path.write_text(_dump(catalog), encoding="utf-8")
    with pytest.raises(CatalogError):
        load_catalog(path)


def test_self_approval_rejected_while_reviewer_undefined(tmp_path: Path):
    # P2 §4.2: reviewer_role='chua_chi_dinh' -> không rule nào được duyet_dung,
    # kể cả khi ai đó tự điền nguoi_duyet vào catalog.
    catalog = load_catalog()
    rule = catalog["rules"][0]
    rule["trang_thai"] = "duyet_dung"
    rule["nguoi_duyet"] = "self"
    rule["ngay_duyet"] = "2026-11-03"
    path = tmp_path / "self_approve.yaml"
    path.write_text(_dump(catalog), encoding="utf-8")
    with pytest.raises(CatalogError):
        load_catalog(path)


def test_duyet_dung_requires_approver_and_date(tmp_path: Path):
    # Khi reviewer_role đã được chỉ định, duyet_dung hợp lệ cần đủ nguoi_duyet + ngay_duyet.
    catalog = load_catalog()
    catalog["reviewer_role"] = "chu_truong_linh_thinh"
    rule = catalog["rules"][0]
    rule["trang_thai"] = "duyet_dung"
    path = tmp_path / "duyet_missing_approver.yaml"
    path.write_text(_dump(catalog), encoding="utf-8")
    with pytest.raises(CatalogError):
        load_catalog(path)

    catalog = load_catalog()
    catalog["reviewer_role"] = "chu_truong_linh_thinh"
    rule = catalog["rules"][0]
    rule["trang_thai"] = "duyet_dung"
    rule["nguoi_duyet"] = "thay_x"
    rule["ngay_duyet"] = "2026-11-03"
    path2 = tmp_path / "duyet_valid.yaml"
    path2.write_text(_dump(catalog), encoding="utf-8")
    loaded = load_catalog(path2)
    assert loaded["rules"][0]["trang_thai"] == "duyet_dung"


# --- P2.TC-09: file nguồn thiếu phải được nhận diện đúng (không lỗi im lặng) ---
def test_missing_source_file_is_explicit(tmp_path: Path):
    catalog = load_catalog()
    catalog["source_file"] = "configs/khong-ton-tai.md"
    path = tmp_path / "missing_source.yaml"
    path.write_text(_dump(catalog), encoding="utf-8")
    with pytest.raises(CatalogError):
        load_catalog(path)


# --- P2.TC-10: nội dung nhạy cảm chưa duyệt không được vào trạng thái "dùng" (I3) ---
def test_sensitive_rule_blocked_from_active_statuses(tmp_path: Path):
    catalog = load_catalog()
    rule = next(r for r in catalog["rules"] if r["noi_dung_nhay_cam"])
    rule["noi_dung_da_duyet"] = False
    rule["trang_thai"] = "chua_ho_tro"
    path = tmp_path / "sensitive_active.yaml"
    path.write_text(_dump(catalog), encoding="utf-8")
    with pytest.raises(CatalogError):
        load_catalog(path)


def test_sensitive_rule_with_content_approval_passes_i3(tmp_path: Path):
    # I3 chỉ chặn khi chưa duyệt nội dung; khi noi_dung_da_duyet=True,
    # trạng thái "chua_ho_tro" (không phải duyet_dung) được phép.
    catalog = load_catalog()
    rule = next(r for r in catalog["rules"] if r["noi_dung_nhay_cam"])
    rule["noi_dung_da_duyet"] = True
    rule["trang_thai"] = "chua_ho_tro"
    path = tmp_path / "sensitive_approved.yaml"
    path.write_text(_dump(catalog), encoding="utf-8")
    loaded = load_catalog(path)
    assert get_rule(loaded, rule["id"])["noi_dung_da_duyet"] is True


# --- P2.TC-11: trần 8 ứng viên bản đầu được thực thi (I5) ---
def test_batch_candidates_cap_is_enforced(tmp_path: Path):
    catalog = load_catalog()
    assert len(batch_candidates(catalog)) == 8
    for rule in catalog["rules"]:
        if rule["san_sang_thuc_thi"] and not rule["noi_dung_nhay_cam"] and not rule["ung_vien_ban_dau"]:
            rule["ung_vien_ban_dau"] = True
            break
    else:
        pytest.fail("Không tìm được rule để đẩy bản đầu vượt trần 8")
    path = tmp_path / "batch_overflow.yaml"
    path.write_text(_dump(catalog), encoding="utf-8")
    with pytest.raises(CatalogError):
        load_catalog(path)


# --- P2.TC-12: thiếu trường bắt buộc của rule phải bị chặn ---
def test_missing_required_rule_field_rejected(tmp_path: Path):
    catalog = load_catalog()
    del catalog["rules"][0]["ca_kiem_thu"]
    path = tmp_path / "missing_field.yaml"
    path.write_text(_dump(catalog), encoding="utf-8")
    with pytest.raises(CatalogError):
        load_catalog(path)


# --- P2.TC-13: cờ boolean viết dạng string trong YAML phải bị chặn ---
def test_non_boolean_flag_rejected(tmp_path: Path):
    catalog = load_catalog()
    catalog["rules"][0]["noi_dung_nhay_cam"] = "false"
    path = tmp_path / "string_flag.yaml"
    path.write_text(_dump(catalog), encoding="utf-8")
    with pytest.raises(CatalogError):
        load_catalog(path)