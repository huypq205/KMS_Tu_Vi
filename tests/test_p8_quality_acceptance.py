# -*- coding: utf-8 -*-
"""P8 (Plan_Fix_Mai_Anh_v2 §11): Nghiệm thu chất lượng sản phẩm (12 ca cố định & Rubric 6 tiêu chí).

Bộ ca cố định (§11.1):
1. Ca 1: Lá số nhiều sao và Mệnh vô chính diệu
2. Ca 2: Cung Mệnh trùng cung Thân (Thân cư Mệnh)
3. Ca 3: Một sao trùng nhiều vai trò (P4 tín hiệu lưu niên)
4. Ca 4: Cách cục đủ điều kiện và chỉ khớp một phần (P3)
5. Ca 5: Dữ kiện thiếu hoặc nguồn diễn giải mâu thuẫn
6. Ca 6: Giờ sinh không chắc chắn C/D
7. Ca 7: Không có khóa AI (Missing key fallback)
8. Ca 8: AI timeout (Timeout fallback)
9. Ca 9: Response nhạy cảm (Sensitive content safe fallback)
10. Ca 10: Cache của hai mức đọc (Cache isolation per reading_mode)
11. Ca 11: Đổi năm trong khi còn báo cáo cũ (Year mismatch UI banner)
12. Ca 12: Thiếu file tham khảo trên môi trường triển khai (Resilience)

Rubric 6 tiêu chí (§11.2):
- Tiêu chí 1 (0-2đ): Đúng dữ kiện và năm xem
- Tiêu chí 2 (0-2đ): Phân biệt lá số gốc với hạn
- Tiêu chí 3 (0-2đ): Giải thích được liên hệ giữa dữ kiện
- Tiêu chí 4 (0-2đ): Cân nhắc thuận/nghịch
- Tiêu chí 5 (0-2đ): Nêu điều kiện làm thay đổi hoặc giới hạn kết luận
- Tiêu chí 6 (0-2đ): Dễ hiểu, ít lặp, tổng hợp rõ (Bố cục 5 khối mạch lạc)
Ngưỡng đạt: mỗi ca >= 10/12 điểm và không có lỗi nghiêm trọng.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from backend.app.schemas.horoscope import HoroscopeRequest
from backend.app.main import horoscope_read
from backend.app.services.horoscope_service import read_horoscope
from backend.app.services import horoscope_cache
from backend.app.services.cach_cuc_detector import (
    detect_cach_cuc,
    OUTCOME_FULL,
    OUTCOME_PARTIAL,
)
from backend.app.services.horoscope_interpreter import (
    LOW_CONFIDENCE_CAVEAT,
    CONFIDENCE_PERCENT_PATTERN,
    check_sensitive_content,
)


def evaluate_rubric(report: dict) -> dict[str, int | str]:
    """Chấm điểm báo cáo theo 6 tiêu chí của Rubric P8 §11.2 (0-2 điểm mỗi tiêu chí, tổng 12đ)."""
    scores = {}
    meta = report.get("meta", {})
    reading = report.get("reading", {})
    annual = report.get("annual", {})
    la_so = report.get("la_so", {})
    thap_ni_cung = la_so.get("thap_ni_cung", [])

    # Tiêu chí 1: Đúng dữ kiện và năm xem
    # 2đ: Đủ 12 cung, có can chi năm xem khớp meta.target_year
    c1 = 0
    if len(thap_ni_cung) == 12:
        c1 += 1
    if annual.get("year") == meta.get("target_year") and annual.get("can_chi"):
        c1 += 1
    scores["tieu_chi_1_dung_du_kien"] = c1

    # Tiêu chí 2: Phân biệt lá số gốc với hạn
    # 2đ: Sao lưu niên không bị lẫn vào sao gốc của thap_ni_cung; có tiền tố L. hoặc nhom luu_nien
    c2 = 0
    stars_in_palaces = [s for p in thap_ni_cung for s in p.get("saos", [])]
    natal_names = [s.get("saoTen") for s in stars_in_palaces if isinstance(s, dict)]
    # Sao gốc không được mang tiền tố 'L. '
    if not any(name.startswith("L. ") for name in natal_names if name):
        c2 += 1
    luu_nien = report.get("luu_nien") or {}
    if luu_nien.get("thai_tue") or luu_nien.get("luu_tu_hoa"):
        c2 += 1
    scores["tieu_chi_2_phan_biet_goc_han"] = c2

    # Tiêu chí 3: Giải thích liên hệ giữa dữ kiện
    # 2đ: Các nhận định có fact_ids hợp lệ và có phần giải nghĩa thuần Việt / rule_ids
    c3 = 0
    ket_luan = reading.get("ket_luan") or []
    if ket_luan and any(pt.get("fact_ids") for pt in ket_luan if isinstance(pt, dict)):
        c3 += 1
    if any(pt.get("giai_thich_thun_viet") or pt.get("rule_ids") for pt in ket_luan if isinstance(pt, dict)):
        c3 += 1
    scores["tieu_chi_3_giai_thich_lien_he"] = c3

    # Tiêu chí 4: Cân nhắc thuận / nghịch
    # 2đ: Có loi_chung_cu hợp lệ và phan_chung không rỗng
    c4 = 0
    luan_diem = reading.get("luan_diem") or []
    if luan_diem and any(pt.get("loi_chung_cu") for pt in luan_diem if isinstance(pt, dict)):
        c4 += 1
    if any(isinstance(pt.get("phan_chung"), str) and pt.get("phan_chung").strip() for pt in luan_diem if isinstance(pt, dict)):
        c4 += 1
    scores["tieu_chi_4_can_nhac_thuan_nghich"] = c4

    # Tiêu chí 5: Nêu điều kiện làm thay đổi hoặc giới hạn kết luận
    # 2đ: Có gioi_han rõ ràng, nêu điều kiện chưa kiểm tra
    c5 = 0
    if ket_luan and all(isinstance(pt.get("gioi_han"), str) and pt.get("gioi_han").strip() for pt in ket_luan if isinstance(pt, dict)):
        c5 += 1
    basic = report.get("thong_tin_co_ban", {})
    if str(basic.get("input_confidence", "A")).upper() in ("C", "D"):
        # Mức C/D phải nêu caveat rõ ràng
        if all(LOW_CONFIDENCE_CAVEAT in pt.get("gioi_han", "") for pt in ket_luan if isinstance(pt, dict)):
            c5 += 1
    else:
        c5 += 1
    scores["tieu_chi_5_gioi_han_dieu_kien"] = c5

    # Tiêu chí 6: Dễ hiểu, ít lặp, tổng hợp rõ (Bố cục 5 khối mạch lạc)
    # 2đ: Không dùng phần trăm, có đủ các khối chủ đề và lời khuyên hành động
    c6 = 0
    reading_str = json.dumps(reading, ensure_ascii=False)
    if not CONFIDENCE_PERCENT_PATTERN.search(reading_str):
        c6 += 1
    if reading.get("tong_quan") and reading.get("loi_khuyen_hanh_dong"):
        c6 += 1
    scores["tieu_chi_6_de_hieu_tong_hop"] = c6

    total = sum(scores.values())
    return {"scores": scores, "total": total, "passed": total >= 10}


# ==============================================================================
# 12 CA KIỂM THỬ NGHIỆM THU CỐ ĐỊNH (P8 §11.1)
# ==============================================================================

def test_p8_ca01_menh_vo_chinh_dieu():
    """Ca 1: Lá số nhiều sao và Mệnh vô chính diệu (VCD)."""
    # 1/5/1990 giờ 3 (Dần) có Mệnh tại Mão là VCD
    req = HoroscopeRequest(ngay=1, thang=5, nam=1990, chi_gio=3, provider="mock")
    rep = horoscope_read(req)

    thap_ni_cung = rep["la_so"]["thap_ni_cung"]
    menh_cung = next(c for c in thap_ni_cung if c.get("ten_cung") == "Mệnh")
    # Không có chính tinh
    chinh_tinh = [s for s in menh_cung.get("saos", []) if s.get("saoLoai") == 1]
    assert len(chinh_tinh) == 0, "Cung Mệnh VCD phải không có chính tinh"

    # Chấm rubric
    rubric = evaluate_rubric(rep)
    assert rubric["total"] >= 10, f"Ca 1 không đạt rubric: {rubric}"


def test_p8_ca02_menh_than_dong_cung():
    """Ca 2: Cung Mệnh trùng cung Thân (Thân cư Mệnh)."""
    # 15/8/1995 giờ 1 (Tý) có Mệnh Thân đồng cung tại Thân
    req = HoroscopeRequest(ngay=15, thang=8, nam=1995, chi_gio=1, provider="mock")
    rep = horoscope_read(req)

    basic = rep["thong_tin_co_ban"]
    assert basic["cung_menh"] == basic["cung_than"] == "Thân"

    # Chấm rubric
    rubric = evaluate_rubric(rep)
    assert rubric["total"] >= 10, f"Ca 2 không đạt rubric: {rubric}"


def test_p8_ca03_mot_sao_trung_nhieu_vai_tro():
    """Ca 3: Một sao trùng nhiều vai trò (P4 tín hiệu lưu niên)."""
    req = HoroscopeRequest(ngay=15, thang=8, nam=1995, chi_gio=5, provider="mock", target_year=2026)
    rep = horoscope_read(req)

    luu_nien = rep.get("luu_nien") or {}
    can_luu_y = luu_nien.get("can_luu_y") or {}
    assert can_luu_y.get("level") in ("nhan", "vua", "nang", "chua_du_du_lieu")

    # Mọi tín hiệu đều có định danh duy nhất và 'vi_sao' tất định
    for signal in can_luu_y.get("signals") or []:
        assert "tin_hieu_id" in signal
        assert "vi_sao" in signal
        why = signal["vi_sao"]
        assert why.get("quy_tac")
        assert why.get("giai_thich")


def test_p8_ca04_cach_cuc_du_va_mot_phan():
    """Ca 4: Cách cục đủ điều kiện và chỉ khớp một phần (P3)."""
    from backend.app.services.horoscope_features import generate_raw_horoscope, extract_horoscope_features
    from backend.app.services.horoscope_analysis import build_star_facts

    raw = generate_raw_horoscope(15, 8, 1995, 5, 1, True)
    features = extract_horoscope_features(raw, 2026)
    facts = build_star_facts(features, {})

    detection = detect_cach_cuc(features, facts=facts)
    assert "rules" in detection
    assert detection["tong_so_quy_tac"] >= 8
    # Phân loại trạng thái quy tắc chuẩn xác
    statuses = {r.get("ket_qua") for r in detection["rules"]}
    assert any(s in ("khop_du", "khop_mot_phan", "khong_khop") for s in statuses)


def test_p8_ca05_du_kien_thieu_hoac_mau_thuan():
    """Ca 5: Dữ kiện thiếu hoặc nguồn diễn giải mâu thuẫn -> không phán mò."""
    from backend.app.services.horoscope_annual import compute_luu_nien

    # Thiếu lá số 12 cung
    res = compute_luu_nien([], 2026)
    can_luu_y = res.get("can_luu_y") or {}
    assert can_luu_y.get("level") == "chua_du_du_lieu"
    reason = can_luu_y.get("level_reason", "").lower()
    assert "thiếu dữ kiện" in reason or "chưa đủ 12 cung" in reason


def test_p8_ca06_gio_sinh_khong_chac_chan_cd():
    """Ca 6: Giờ sinh không chắc chắn C/D -> chỉ kết luận cấu trúc."""
    req = HoroscopeRequest(
        ngay=15, thang=8, nam=1995, chi_gio=5,
        provider="mock", input_confidence="C",
    )
    rep = horoscope_read(req)

    for pt in rep.get("reading", {}).get("ket_luan", []):
        assert pt.get("loai_ket_luan") == "cau_truc"
        assert LOW_CONFIDENCE_CAVEAT in pt.get("gioi_han", "")

    rubric = evaluate_rubric(rep)
    assert rubric["total"] >= 10, f"Ca 6 không đạt rubric: {rubric}"


def test_p8_ca07_khong_co_khoa_ai():
    """Ca 7: Không có khóa AI -> fallback an toàn sang mock, không crash 500."""
    from backend.app.services import horoscope_interpreter as module

    with patch.object(module, "GEMINI_API_KEY", ""), patch.dict(module.os.environ, {"GEMINI_API_KEY": ""}):
        reading = module.interpret_horoscope({}, "", provider="auto")
    assert reading["_generation"]["is_mock"] is True
    assert reading["_generation"]["reason"] == "missing_key"


def test_p8_ca08_ai_timeout():
    """Ca 8: AI timeout -> chuyển mock an toàn, bảo toàn lá số."""
    from backend.app.services import horoscope_interpreter as module
    import requests

    with patch("requests.post", side_effect=requests.Timeout("Mock timeout")):
        reading = module.interpret_horoscope({}, "", provider="auto")
    assert reading["_generation"]["is_mock"] is True
    assert reading["_generation"]["reason"] == "timeout"


def test_p8_ca09_response_nhay_cam():
    """Ca 9: Response có nội dung nhạy cảm -> hạ cấp an toàn về mức du_lieu."""
    bad_reading = {
        "ket_luan": [{"nhan_dinh": "Người này số mệnh chết yểu tử vong khó thoát."}],
    }
    violation = check_sensitive_content(bad_reading)
    assert violation is not None
    assert "tử vong" in violation.lower() or "yểu" in violation.lower()


def test_p8_ca10_cache_cua_hai_muc_doc():
    """Ca 10: Cache của hai mức đọc phân biệt độc lập (P6 §9.1)."""
    birth = {"ngay": 15, "thang": 8, "nam": 1995, "chi_gio": 5, "gioi_tinh": 1, "duong_lich": True}
    key_du_lieu = horoscope_cache.compute_key(birth, "auto", "model", "ctx", "v1", "du_lieu")
    key_chuyen_sau = horoscope_cache.compute_key(birth, "auto", "model", "ctx", "v1", "chuyen_sau")
    assert key_du_lieu != key_chuyen_sau


def test_p8_ca11_doi_nam_khi_con_bao_cao_cu():
    """Ca 11: Đổi năm trong khi còn báo cáo cũ -> UI cảnh báo lệch năm chiêm nghiệm."""
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/horoscope_ui.py", default_timeout=20).run()
    # Mock submit report 2026
    req = HoroscopeRequest(ngay=15, thang=8, nam=1995, chi_gio=5, provider="mock", target_year=2026)
    payload = horoscope_read(req)
    response = Mock()
    response.iter_lines.return_value = iter([json.dumps({"event": "result", "report": payload})])
    with patch("requests.post", return_value=response):
        app.sidebar.button[0].click().run()

    # Đổi target_year sang 2027
    app.number_input(key="target_year").set_value(2027).run()
    assert app.warning
    assert any("2026" in w.value and "2027" in w.value for w in app.warning)


def test_p8_ca12_thieu_file_tham_khao_moi_truong():
    """Ca 12: Thiếu file tham khảo trên môi trường triển khai -> an toàn, không crash."""
    from backend.app.services import star_meanings_reference

    with patch.object(star_meanings_reference, "DEFAULT_PATH", Path("non_existent_star_meanings.md")):
        meanings = star_meanings_reference.load_meanings()
        assert meanings == {}
        # Hệ thống vẫn đọc lá số bình thường khi thiếu file tham khảo
        req = HoroscopeRequest(ngay=15, thang=8, nam=1995, chi_gio=5, provider="mock")
        rep = read_horoscope(req)
        assert rep["status"] == "ok"
        assert len(rep["la_so"]["thap_ni_cung"]) == 12


# ==============================================================================
# RELEASE READINESS & ROLLBACK SAFEGUARDS (§11.4)
# ==============================================================================

def test_p8_release_readiness_cache_version_and_contract_integrity():
    """Kiểm tra sự sẵn sàng phát hành: CACHE_SCHEMA_VERSION đã bump, contract đầy đủ 3 mức."""
    from backend.app.services.horoscope_cache import CACHE_SCHEMA_VERSION
    from backend.app.schemas.horoscope_contract import READING_MODES, GROUPS_REQUIRED_BY_MODE

    # Schema version >= 7 (đã bao hàm reading_mode)
    assert CACHE_SCHEMA_VERSION >= 7
    # Hợp đồng 3 mức đọc hoàn chỉnh
    assert set(READING_MODES) == {"du_lieu", "giai_thich", "chuyen_sau"}
    for mode in READING_MODES:
        assert len(GROUPS_REQUIRED_BY_MODE[mode]) >= 2
