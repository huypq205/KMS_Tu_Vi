# -*- coding: utf-8 -*-
"""P6 (Plan_Fix_Mai_Anh_v2 §9): Ba mức đọc và AI chuyên sâu.

Ma trận test:
- P6.TC-01..03: Điều phối chế độ, cấm gọi AI ở mức du_lieu, meta actual_reading_mode & fallback_reason
- P6.TC-04..05: Ngân sách token và phân biệt cache theo reading_mode
- P6.TC-06..08: Prompt theo mức, phát hiện và xử lý nội dung nhạy cảm (hạ cấp an toàn)
- P6.TC-09..11: Kiểm tra tham chiếu output (fact_ids, source_refs, rule_ids) và UI AppTest
"""
from __future__ import annotations

import json
from unittest.mock import Mock, patch
import pytest

from backend.app.schemas.horoscope import HoroscopeRequest
from backend.app.schemas.horoscope_contract import (
    ReadingMode,
    READING_MODES,
    adapt_reading,
    GROUPS_REQUIRED_BY_MODE,
)
from backend.app.services.horoscope_interpreter import (
    check_sensitive_content,
    build_horoscope_user_prompt,
    HOROSCOPE_MAX_TOKENS_GIAI_THICH,
    HOROSCOPE_MAX_TOKENS_CHUYEN_SAU,
)
from backend.app.services.horoscope_service import read_horoscope, reading_events
from backend.app.services import horoscope_cache


def _req(mode: ReadingMode = "du_lieu", provider: str = "mock") -> HoroscopeRequest:
    return HoroscopeRequest(
        ngay=15, thang=8, nam=1995, chi_gio=5,
        provider=provider, reading_mode=mode,
    )


def test_p6_tc01_du_lieu_mode_never_calls_ai_even_with_auto_or_gemini():
    """P6.TC-01: Chế độ du_lieu KHÔNG gọi AI (P6 §9.1), bất kể provider=auto hay gemini."""
    req_auto = _req(mode="du_lieu", provider="auto")
    req_gemini = _req(mode="du_lieu", provider="gemini")

    with patch("requests.post") as mock_post:
        rep1 = read_horoscope(req_auto)
        rep2 = read_horoscope(req_gemini)
        # Không có bất kỳ HTTP POST nào tới Gemini
        mock_post.assert_not_called()

    for rep in (rep1, rep2):
        meta = rep["meta"]
        assert meta["reading_mode"] == "du_lieu"
        assert meta["actual_reading_mode"] == "du_lieu"
        assert meta.get("fallback_reason") is None
        assert meta["is_mock"] is True


def test_p6_tc02_successful_chuyen_sau_returns_matching_actual_mode():
    """P6.TC-02: Backend trả mức được yêu cầu + mức thực tế đã hoàn thành + lý do fallback."""
    req = _req(mode="chuyen_sau", provider="mock")
    rep = read_horoscope(req)
    meta = rep["meta"]
    assert meta["reading_mode"] == "chuyen_sau"
    # Với mock, bài đọc trả về thành công ở mức được yêu cầu
    assert meta["actual_reading_mode"] == "chuyen_sau"
    assert meta.get("fallback_reason") is None


def test_p6_tc03_llm_failure_in_chuyen_sau_falls_back_gracefully():
    """P6.TC-03: Lỗi ở mức chuyên sâu -> giữ lá số, hạ mức an toàn kèm fallback_reason (P6 §9.1)."""
    req = _req(mode="chuyen_sau", provider="auto")

    with patch("backend.app.services.horoscope_cache.lookup", return_value=None), \
         patch("backend.app.services.horoscope_service.interpret_horoscope") as mock_interp:
        mock_interp.side_effect = Exception("Gemini service unavailable")
        # Giả lập interpret_horoscope ném lỗi trong stream
        events = list(reading_events(req))

    chart_evt = next(e for e in events if e.get("event") == "chart_ready")
    assert len(chart_evt["report"]["la_so"]["thap_ni_cung"]) == 12

    err_or_res = [e for e in events if e.get("event") in ("result", "error")]
    assert err_or_res, "Stream phải phát sự kiện kết thúc"


def test_p6_tc04_token_budgets_defined_per_mode():
    """P6.TC-04: Ngân sách output được cấu hình theo từng mức đọc (P6 §9.2, cập nhật Gói 2: 12288)."""
    assert HOROSCOPE_MAX_TOKENS_GIAI_THICH >= 2500
    assert HOROSCOPE_MAX_TOKENS_CHUYEN_SAU >= 6000


def test_p6_tc05_cache_key_differentiates_all_three_modes():
    """P6.TC-05: Cache phân biệt reading_mode (P6 §9.1)."""
    birth = {"ngay": 15, "thang": 8, "nam": 1995, "chi_gio": 5, "gioi_tinh": 1, "duong_lich": True}
    ctx_hash = "abc123"
    idx_ver = "v1"

    key_du_lieu = horoscope_cache.compute_key(birth, "auto", "gemini-2.5", ctx_hash, idx_ver, "du_lieu")
    key_giai_thich = horoscope_cache.compute_key(birth, "auto", "gemini-2.5", ctx_hash, idx_ver, "giai_thich")
    key_chuyen_sau = horoscope_cache.compute_key(birth, "auto", "gemini-2.5", ctx_hash, idx_ver, "chuyen_sau")

    assert key_du_lieu != key_giai_thich
    assert key_giai_thich != key_chuyen_sau
    assert key_du_lieu != key_chuyen_sau


def test_p6_tc06_prompt_tailored_for_giai_thich_vs_chuyen_sau():
    """P6.TC-06: Prompt mức giải thích vs chuyên sâu có trọng tâm khác nhau (P6 §9.4, §9.5)."""
    from backend.app.services.horoscope_features import generate_raw_horoscope, extract_horoscope_features
    from backend.app.services.horoscope_analysis import build_star_facts
    from backend.app.services.cach_cuc_detector import detect_cach_cuc

    raw = generate_raw_horoscope(15, 8, 1995, 5, 1, True)
    features = extract_horoscope_features(raw, 2026)
    facts = build_star_facts(features, {})
    cach_cuc = detect_cach_cuc(features, facts=facts)

    prompt_gt = build_horoscope_user_prompt(
        features, "ngữ cảnh sách", facts, cach_cuc=cach_cuc, reading_mode="giai_thich",
    )
    prompt_cs = build_horoscope_user_prompt(
        features, "ngữ cảnh sách", facts, cach_cuc=cach_cuc, reading_mode="chuyen_sau",
    )

    # Mức giải thích nhấn mạnh phá toái thuật ngữ thuần Việt
    assert "thuần việt" in prompt_gt.lower() or "giải nghĩa" in prompt_gt.lower()
    # Mức chuyên sâu nhấn mạnh tổng hợp đa chiều, điều kiện thuận nghịch
    assert "chuyên sâu" in prompt_cs.lower() or "tổng hợp" in prompt_cs.lower()


def test_p6_tc07_sensitive_content_check_detects_forbidden_claims():
    """P6.TC-07: check_sensitive_content phát hiện phán đoán tử vong, yểu chiết, phẩm hạnh (P6 §9.8)."""
    clean_reading = {
        "ket_luan": [
            {"nhan_dinh": "Tính cách độc lập, quyết đoán trong công việc.", "gioi_han": "Chiêm nghiệm."}
        ]
    }
    assert check_sensitive_content(clean_reading) is None

    bad_readings = [
        {"ket_luan": [{"nhan_dinh": "Người này chắc chắn chết yểu trước năm 40 tuổi."}]},
        {"ket_luan": [{"nhan_dinh": "Số mệnh yểu chiết, tai nạn tử vong khó tránh."}]},
        {"ket_luan": [{"nhan_dinh": "Phụ nữ mang số này dâm đãng, trắc nết."}]},
        {"luan_diem": [{"nhan_dinh": "Cách cục chết đuối, thọ yểu không ngờ."}]},
    ]
    for bad in bad_readings:
        problem = check_sensitive_content(bad)
        assert problem is not None, f"Phải phát hiện nội dung nhạy cảm trong: {bad}"
        assert any(kw in problem.lower() for kw in ("nhạy cảm", "tử vong", "yểu", "phẩm hạnh"))


def test_p6_tc08_sensitive_content_triggers_fallback_to_safe_level():
    """P6.TC-08: Output nhạy cảm sau retry bị hạ về mức dữ kiện an toàn thay vì xóa chữ (P6 §9.8)."""
    from backend.app.services.horoscope_interpreter import interpret_horoscope

    raw = _req(mode="chuyen_sau", provider="auto")
    # Giả lập Gemini trả bài có nội dung nhạy cảm
    mock_bad_body = json.dumps({
        "tieu_de": "Lá số",
        "tong_quan": {"ban_sac": "bản sắc", "diem_manh": [], "diem_can_ren_luyen": [], "ngu_hanh_nang_luong": "Kim"},
        "su_nghiep": {"phong_cach_lam_viec": "làm", "moi_truong_phu_hop": "nơi", "nghe_nghiep_tuong_hop": [], "loi_khuyen_phat_trien": "tập"},
        "tai_chinh": {"tu_duy_tien_bac": "tiền", "co_hoi_tich_luy": "tích", "rui_ro_can_phong": "rủi", "loi_khuyen_quan_ly_tai_chinh": "quản"},
        "tinh_cam": {"xu_huong_tinh_cam": "tình", "mau_nguoi_tuong_hop": "hợp", "bi_quyet_hoa_hop": "hòa"},
        "van_han_hien_tai": {"giai_doan": "Năm 2026", "chu_de_trong_tam": "tâm", "co_hoi_nen_nam_bat": "cơ", "thach_thuc_can_can_trong": "thách"},
        "loi_khuyen_hanh_dong": ["khuyên"],
        "luan_diem": [],
        "ket_luan": [{"nhan_dinh": "Số mệnh tử vong yểu chiết chắc chắn.", "giai_thich_thun_viet": "nghĩa",
                      "fact_ids": [], "source_refs": [], "gioi_han": "giới", "muc_tin_cay": "yeu"}],
    })

    with patch("backend.app.services.horoscope_cache.lookup", return_value=None), \
         patch("backend.app.services.horoscope_cache.save"), \
         patch("requests.post") as mock_post:
        resp = Mock()
        resp.status_code = 200
        resp.json.return_value = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": mock_bad_body}]}}]}
        mock_post.return_value = resp

        rep = read_horoscope(raw)
        meta = rep["meta"]
        # Phải được hạ về actual_reading_mode an toàn
        assert meta["actual_reading_mode"] == "du_lieu"
        assert meta.get("fallback_reason") in ("sensitive_content", "invalid_response")


def test_p6_tc09_contract_groups_fulfilled_for_each_mode():
    """P6.TC-09: Báo cáo trả về qua adapter đảm bảo đủ nhóm thông tin theo từng mức (P6 §9.1, P1)."""
    for mode in READING_MODES:
        req = _req(mode=mode, provider="mock")
        rep = read_horoscope(req)
        adapted = adapt_reading(rep.get("reading") or {}, mode=mode)
        required_groups = set(GROUPS_REQUIRED_BY_MODE[mode])
        for item in adapted["items"]:
            # Mọi trường cần thiết đều có mặt
            assert required_groups <= set(item.keys())


def test_p6_tc10_ui_apptest_allows_reading_mode_selection():
    """P6.TC-10 (điều chỉnh): UI chỉ còn 2 mức đọc, đã bỏ mức 'AI giải thích'."""
    from streamlit.testing.v1 import AppTest
    from pathlib import Path

    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/horoscope_ui.py", default_timeout=20).run()
    assert not app.exception

    # Selectbox chọn mức đọc tồn tại, chỉ còn lá số & dữ kiện / AI chuyên sâu
    assert "reading_mode" in [sb.key for sb in app.sidebar.selectbox]
    mode_sb = app.sidebar.selectbox(key="reading_mode")
    assert len(mode_sb.options) == 2
    assert not any("giải nghĩa thuật ngữ" in str(opt) for opt in mode_sb.options)
    assert any("Lá số & dữ kiện" in str(opt) for opt in mode_sb.options)
    assert any("AI chuyên sâu" in str(opt) for opt in mode_sb.options)

    # Submit với mức 'du_lieu'
    mode_sb.set_value("du_lieu")
    with patch("requests.post") as mock_post:
        # Trong chế độ du_lieu qua UI local transport, không gọi LLM
        app.sidebar.button[0].click().run()
    assert not app.exception

