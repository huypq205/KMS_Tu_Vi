"""P3 (Plan_Fix_Mai_Anh_v2): nhận diện cách cục bằng code trên dữ kiện lá số.

Phạm vi bản đầu: 8 quy tắc ``ung_vien_ban_dau`` của danh mục P2. Bộ nhận diện:

- chỉ đọc dữ kiện đã an (sao, cung, quan hệ P2b, trạng thái sao, tầng thời gian);
- liên kết kết quả với ``fact_id`` của ``build_star_facts``;
- phân biệt khớp đủ / khớp một phần / không khớp / chưa thể đánh giá;
- không lấy sao lưu niên ghép với sao gốc cho quy tắc ``la_so_goc``;
- không tự duyệt quy tắc: trạng thái nội dung giữ nguyên ``chi_tham_khao``;
- ghi nhận dữ kiện bị nhiều quy tắc dùng và điều kiện thuận/nghịch.

Ranh giới P3: không đổi bảng trạng thái sao hay bảng Tứ Hóa (P2b §5.3); không
thay nội dung nguồn P2.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from backend.app.schemas.horoscope_contract import MISSING, adapt_reading
from backend.app.services.cach_cuc_catalog import (
    CatalogError,
    batch_candidates,
    get_rule,
    load_catalog,
)
from backend.app.services.cach_cuc_detector import (
    CONDITION_DAT,
    CONDITION_KHONG_DAT,
    CONDITION_UNKNOWN,
    OUTCOME_FULL,
    OUTCOME_NONE,
    OUTCOME_PARTIAL,
    OUTCOME_UNKNOWN,
    OUTCOMES,
    check_rule_ids,
    detect_cach_cuc,
)
from backend.app.services.horoscope_analysis import build_star_facts
from backend.app.services.palace_relations import CHI_NAMES

ROLE_BY_SO = {
    1: "Tài Bạch", 2: "Tử tức", 3: "Phu thê", 4: "Huynh đệ",
    5: "Mệnh", 6: "Phụ mẫu", 7: "Phúc đức", 8: "Điền trạch",
    9: "Quan lộc", 10: "Nô bộc", 11: "Thiên di", 12: "Tật ách",
}


def star(name: str, dac_tinh: str = "—") -> dict:
    return {"ten": name, "dac_tinh": dac_tinh}


def _features(placements: dict[int, list[dict]], *, annual: dict | None = None,
              can_chi_nam: str | None = "Ất Hợi") -> dict:
    """Lá số tổng hợp đủ 12 cung; placements = {cung_so: [sao...]}."""
    palaces = []
    for so in range(1, 13):
        palaces.append({
            "cung_so": so,
            "ten": ROLE_BY_SO[so],
            "chuan_ten": CHI_NAMES[so - 1],
            "tuan_trung": False,
            "triet_lo": False,
            "chinh_tinh": placements.get(so, []),
            "cat_tinh": [],
            "sat_tinh": [],
            "phu_tinh_khac": [],
            "risk_stars": [],
        })
    basic = {"tu_hoa_table": {"id": "lasotuvi"}}
    if can_chi_nam is not None:
        basic["can_chi_nam"] = can_chi_nam
    return {
        "thong_tin_co_ban": basic,
        "palaces": palaces,
        "luu_nien": annual or {},
    }


def _detect(placements: dict[int, list[dict]], *, annual: dict | None = None,
            can_chi_nam: str | None = "Ất Hợi"):
    features = _features(placements, annual=annual, can_chi_nam=can_chi_nam)
    facts = build_star_facts(features, {})
    return detect_cach_cuc(features, facts=facts), facts, features


def _rule_result(detection: dict, rule_id: str) -> dict:
    return next(r for r in detection["rules"] if r["rule_id"] == rule_id)


def _condition(result: dict, code: str) -> dict:
    return next(c for c in result["dieu_kien"] if c["ma"] == code)


def _fact_id(facts: list[dict], star_name: str, chi: str) -> str:
    return next(f["fact_id"] for f in facts
                if f["sao"].casefold() == star_name.casefold() and f["dia_chi"] == chi)


def _dump(catalog: dict) -> str:
    return yaml.safe_dump(catalog, allow_unicode=True, sort_keys=False)


# --- P3.TC-01: đúng 8 quy tắc bản đầu; không tự duyệt nội dung ---------------
def test_tc01_detects_exactly_eight_batch_candidates_without_approval():
    detection, _, _ = _detect({})
    catalog = load_catalog()
    assert [r["rule_id"] for r in detection["rules"]] == [r["id"] for r in batch_candidates(catalog)]
    assert len(detection["rules"]) == 8
    assert all(r["trang_thai_noi_dung"] == "chi_tham_khao" for r in detection["rules"])
    assert all(r["trang_thai_noi_dung"] != "duyet_dung" for r in detection["rules"])
    assert all(r["ket_qua"] in OUTCOMES for r in detection["rules"])
    assert sum(detection["tom_tat"].values()) == 8
    assert detection["catalog_signature"]


# --- P3.TC-02: dương tính Tử Phủ đồng cung tại Dần ---------------------------
def test_tc02_tu_pu_dong_cung_positive():
    detection, facts, _ = _detect({3: [star("Tử Vi", "M"), star("Thiên Phủ", "M")]})
    result = _rule_result(detection, "quy-tu-pu-dong-cung")
    assert result["ket_qua"] == OUTCOME_FULL
    assert _condition(result, "quan_he")["trang_thai"] == CONDITION_DAT
    assert _condition(result, "chi")["trang_thai"] == CONDITION_DAT
    assert set(result["fact_ids"]) == {
        _fact_id(facts, "Tử Vi", "Dần"),
        _fact_id(facts, "Thiên Phủ", "Dần"),
    }
    assert result["ly_do"]


# --- P3.TC-03: âm tính/thiếu một sao ----------------------------------------
def test_tc03_missing_star_is_not_a_match():
    detection, facts, _ = _detect({3: [star("Tử Vi")]})
    result = _rule_result(detection, "quy-tu-pu-dong-cung")
    assert result["ket_qua"] == OUTCOME_NONE
    assert _condition(result, "sao:Thiên Phủ")["trang_thai"] == CONDITION_KHONG_DAT
    assert result["fact_ids"] == [_fact_id(facts, "Tử Vi", "Dần")]


# --- P3.TC-04: sai cung (đồng cung nhưng không thuộc Dần/Thân) ---------------
def test_tc04_wrong_branch_is_not_a_match():
    detection, _, _ = _detect({1: [star("Tử Vi"), star("Thiên Phủ")]})
    result = _rule_result(detection, "quy-tu-pu-dong-cung")
    assert result["ket_qua"] == OUTCOME_NONE
    assert _condition(result, "quan_he")["trang_thai"] == CONDITION_DAT
    branch = _condition(result, "chi")
    assert branch["trang_thai"] == CONDITION_KHONG_DAT
    assert branch["gia_tri_thuc_te"] == "Tý"


# --- P3.TC-05: sai quan hệ (hai sao ở hai cung khác nhau) -------------------
def test_tc05_wrong_relation_reports_actual_relation():
    detection, _, _ = _detect({3: [star("Tử Vi")], 7: [star("Thiên Phủ")]})
    result = _rule_result(detection, "quy-tu-pu-dong-cung")
    assert result["ket_qua"] == OUTCOME_NONE
    relation = _condition(result, "quan_he")
    assert relation["trang_thai"] == CONDITION_KHONG_DAT
    assert relation["quan_he_thuc_te"] == "tam_hop"


# --- P3.TC-06: quan hệ tam hợp hợp lệ (Lộc Mã giao trì) ---------------------
def test_tc06_tam_hop_relation_matches():
    # Lộc Tồn tại Tý (1), Thiên Mã tại Thìn (5): cùng nhóm tam hợp Tý–Thìn–Thân.
    detection, _, _ = _detect({1: [star("Lộc Tồn")], 5: [star("Thiên Mã")]})
    result = _rule_result(detection, "quy-loc-ma-giao-chi")
    assert result["ket_qua"] == OUTCOME_FULL
    assert _condition(result, "quan_he")["trang_thai"] == CONDITION_DAT


# --- P3.TC-07: trạng thái miếu/vượng thiếu -> chưa thể đánh giá, không suy --
def test_tc07_missing_dignity_is_unknown_not_guess():
    detection, _, _ = _detect({3: [star("Thất Sát", "—")]})
    result = _rule_result(detection, "quy-that-sat-trieu-dau")
    assert result["ket_qua"] == OUTCOME_UNKNOWN
    dignity = _condition(result, "trang_thai_sao:Thất Sát")
    assert dignity["trang_thai"] == CONDITION_UNKNOWN
    assert dignity["gia_tri_thuc_te"] == MISSING
    assert result["dieu_kien_chua_kiem_tra"]


# --- P3.TC-08: đủ cung nhưng sai trạng thái -> khớp một phần ----------------
def test_tc08_wrong_dignity_is_partial_match():
    detection, _, _ = _detect({3: [star("Thất Sát", "H")]})
    result = _rule_result(detection, "quy-that-sat-trieu-dau")
    assert result["ket_qua"] == OUTCOME_PARTIAL
    assert _condition(result, "chi")["trang_thai"] == CONDITION_DAT
    assert _condition(result, "trang_thai_sao:Thất Sát")["trang_thai"] == CONDITION_KHONG_DAT


# --- P3.TC-09: đủ cung + miếu -> khớp đủ ------------------------------------
def test_tc09_right_dignity_is_full_match():
    detection, _, _ = _detect({3: [star("Thất Sát", "M")]})
    result = _rule_result(detection, "quy-that-sat-trieu-dau")
    assert result["ket_qua"] == OUTCOME_FULL
    assert _condition(result, "trang_thai_sao:Thất Sát")["trang_thai"] == CONDITION_DAT


# --- P3.TC-10: không trộn sao lưu niên với sao gốc --------------------------
def test_tc10_annual_star_never_satisfies_natal_rule():
    annual = {"vong_thai_tue": {"that_sat": {
        "ten": "Thất Sát", "cung_so": 3, "cung_ten": "Phu thê", "dia_chi": "Dần",
    }}}
    detection, facts, _ = _detect({1: [star("Tử Vi")]}, annual=annual)
    result = _rule_result(detection, "quy-that-sat-trieu-dau")
    assert result["ket_qua"] == OUTCOME_NONE
    assert result["fact_ids"] == []
    annual_fact = next(f for f in facts if f["nhom"] == "luu_nien")
    assert annual_fact["fact_id"] not in result["fact_ids"]


# --- P3.TC-11: quy tắc ngoài tầng lá số gốc -> chưa thể đánh giá ------------
def test_tc11_time_scope_outside_natal_is_explicitly_unknown():
    catalog = load_catalog()
    rule = dict(get_rule(catalog, "quy-tu-pu-dong-cung"))
    rule["tang_thoi_gian"] = "luu_nien"
    features = _features({3: [star("Tử Vi"), star("Thiên Phủ")]})
    detection = detect_cach_cuc(features, catalog=catalog, rules=[rule],
                                facts=build_star_facts(features, {}))
    result = detection["rules"][0]
    assert result["ket_qua"] == OUTCOME_UNKNOWN
    assert result["dieu_kien_chua_kiem_tra"]
    assert "tầng thời gian" in result["ly_do"]


# --- P3.TC-12: ba Tứ Hóa hội tam phương của một cung -----------------------
def test_tc12_three_tu_hoa_in_tam_phuong_matches():
    detection, _, _ = _detect({
        1: [star("Hóa Khoa")], 5: [star("Hóa Quyền")], 9: [star("Hóa Lộc")],
    })
    result = _rule_result(detection, "quy-khoa-quyen-loc-hoi")
    assert result["ket_qua"] == OUTCOME_FULL
    assert _condition(result, "quan_he")["trang_thai"] == CONDITION_DAT


# --- P3.TC-13: thiếu một trong ba Tứ Hóa -> không khớp ---------------------
def test_tc13_two_of_three_tu_hoa_is_not_a_match():
    detection, _, _ = _detect({1: [star("Hóa Khoa")], 5: [star("Hóa Quyền")]})
    result = _rule_result(detection, "quy-khoa-quyen-loc-hoi")
    assert result["ket_qua"] == OUTCOME_NONE
    assert _condition(result, "sao:Hóa Lộc")["trang_thai"] == CONDITION_KHONG_DAT


# --- P3.TC-14: can tuổi là điều kiện thuận, không phải bắt buộc -------------
def test_tc14_birth_stem_is_a_favourable_condition_not_a_requirement():
    detection, _, _ = _detect({4: [star("Thiên Cơ"), star("Cự Môn")]}, can_chi_nam="Canh Ngọ")
    result = _rule_result(detection, "quy-co-cu-dong-cung-mao")
    assert result["ket_qua"] == OUTCOME_FULL
    favourable = next(c for c in result["dieu_kien_thuan"] if c["ma"] == "can_tuoi")
    assert favourable["trang_thai"] == CONDITION_KHONG_DAT

    detection2, _, _ = _detect({4: [star("Thiên Cơ"), star("Cự Môn")]}, can_chi_nam="Tân Mùi")
    result2 = _rule_result(detection2, "quy-co-cu-dong-cung-mao")
    assert result2["ket_qua"] == OUTCOME_FULL
    favourable2 = next(c for c in result2["dieu_kien_thuan"] if c["ma"] == "can_tuoi")
    assert favourable2["trang_thai"] == CONDITION_DAT


# --- P3.TC-15: cùng một fact bị nhiều quy tắc dùng -------------------------
def test_tc15_fact_reused_by_multiple_rules_is_reported():
    # Vũ Khúc tại Sửu dùng cho cả Tham Vũ đồng hành và Vũ Khúc miếu viên.
    detection, facts, _ = _detect({2: [star("Tham Lang"), star("Vũ Khúc", "M")]})
    vu_khuc_fact = _fact_id(facts, "Vũ Khúc", "Sửu")
    entry = next(e for e in detection["fact_reuse"] if e["fact_id"] == vu_khuc_fact)
    assert set(entry["rule_ids"]) == {"quy-tham-vo-dong-hanh", "quy-vu-khuc-mieu-vien"}
    assert _rule_result(detection, "quy-tham-vo-dong-hanh")["ket_qua"] == OUTCOME_FULL
    assert _rule_result(detection, "quy-vu-khuc-mieu-vien")["ket_qua"] == OUTCOME_NONE


# --- P3.TC-16: lá số thiếu dữ liệu an sao -> chưa thể đánh giá --------------
def test_tc16_empty_star_data_is_unknown_for_every_rule():
    detection, _, _ = _detect({})
    assert all(r["ket_qua"] == OUTCOME_UNKNOWN for r in detection["rules"])
    assert all(r["dieu_kien_chua_kiem_tra"] for r in detection["rules"])


# --- P3.TC-17: thiếu cung (không đủ 12) -> chưa thể đánh giá ---------------
def test_tc17_incomplete_palace_set_is_unknown():
    features = _features({3: [star("Tử Vi"), star("Thiên Phủ")]})
    features["palaces"] = features["palaces"][:11]
    detection = detect_cach_cuc(features, facts=build_star_facts(features, {}))
    assert all(r["ket_qua"] == OUTCOME_UNKNOWN for r in detection["rules"])


# --- P3.TC-18: AI chỉ được dẫn rule_id có trong kết quả nhận diện ----------
def test_tc18_check_rule_ids_accepts_detected_and_rejects_invented():
    detection, _, _ = _detect({3: [star("Tử Vi"), star("Thiên Phủ")]})
    good = {"luan_diem": [{"rule_ids": ["quy-tu-pu-dong-cung"]}], "ket_luan": []}
    assert check_rule_ids(good, detection) is None
    # MISSING/None: báo cáo cũ chưa có trường -> bỏ qua, không bịa.
    legacy = {"luan_diem": [{"rule_ids": MISSING}, {}], "ket_luan": []}
    assert check_rule_ids(legacy, detection) is None
    invented = {"luan_diem": [{"rule_ids": ["quy-khong-ton-tai"]}], "ket_luan": []}
    assert check_rule_ids(invented, detection)


def test_tc18b_check_rule_ids_rejects_rule_that_does_not_match():
    detection, _, _ = _detect({3: [star("Tử Vi")], 7: [star("Thiên Phủ")]})
    reading = {"luan_diem": [{"rule_ids": ["quy-tu-pu-dong-cung"]}], "ket_luan": []}
    assert check_rule_ids(reading, detection)


# --- P3.TC-19: báo cáo offline mang kết quả code + rule_ids vào hợp đồng ---
def test_tc19_mock_report_carries_detection_and_contract_rule_ids():
    from backend.app.services.horoscope_interpreter import generate_mock_reading

    features = _features({3: [star("Tử Vi", "M"), star("Thiên Phủ", "M")]})
    reading = generate_mock_reading(features)
    assert "cach_cuc" in reading
    assert reading["cach_cuc"]["tom_tat"][OUTCOME_FULL] >= 1
    point = next(p for p in reading["ket_luan"] if "Phu thê" in p["nhan_dinh"])
    assert "quy-tu-pu-dong-cung" in point["rule_ids"]
    assert isinstance(point["dieu_kien_chua_kiem_tra"], list)
    contract = adapt_reading(reading, "chuyen_sau")
    item = next(i for i in contract["items"]
                if "quy-tu-pu-dong-cung" in (i["can_cu"]["rule_ids"] or []))
    assert item["can_cu"]["rule_ids"] == point["rule_ids"]


# --- P3.TC-20: prompt nêu cách cục đã nhận diện và cấm AI tự thêm ----------
def test_tc20_prompt_contains_detected_patterns_and_no_invention_rule():
    from backend.app.services.horoscope_interpreter import build_horoscope_user_prompt

    features = _features({3: [star("Tử Vi"), star("Thiên Phủ")]})
    facts = build_star_facts(features, {})
    detection = detect_cach_cuc(features, facts=facts)
    prompt = build_horoscope_user_prompt(features, "", facts, cach_cuc=detection)
    assert "Tử Phủ đồng cung" in prompt
    assert "quy-tu-pu-dong-cung" in prompt
    assert "không tự thêm" in prompt.lower()


# --- P3.TC-21: validator danh mục chặn trạng thái sao sai ------------------
def test_tc21_catalog_rejects_invalid_dignity_requirement(tmp_path: Path):
    catalog = load_catalog()
    catalog["rules"][0]["trang_thai_sao"] = {"Tử Vi": "sai"}
    path = tmp_path / "bad_dignity.yaml"
    path.write_text(_dump(catalog), encoding="utf-8")
    with pytest.raises(CatalogError):
        load_catalog(path)


def test_tc21b_catalog_rejects_dignity_for_star_outside_rule(tmp_path: Path):
    catalog = load_catalog()
    catalog["rules"][0]["trang_thai_sao"] = {"Thất Sát": "mieu"}
    path = tmp_path / "foreign_dignity.yaml"
    path.write_text(_dump(catalog), encoding="utf-8")
    with pytest.raises(CatalogError):
        load_catalog(path)
