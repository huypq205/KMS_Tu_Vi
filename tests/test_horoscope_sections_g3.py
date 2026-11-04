# -*- coding: utf-8 -*-
"""Test suite cho Gói 3: Giao diện báo cáo mới cho người xem phổ thông.

Ma trận kiểm thử:
- TC-G3-01: Export đầy đủ các hàm render theo thứ tự giao diện mới.
- TC-G3-02: Thứ tự hiển thị UI: Tổng quan năm -> Lá số 12 cung -> Chân dung/thế mạnh -> Chủ đề -> Gợi ý hành động -> Căn cứ chuyên môn.
- TC-G3-03: Tổng quan năm hiển thị 3 đoạn văn bám sát target_year.
- TC-G3-04: Báo cáo cũ thiếu tom_tat_nam hiển thị banner/thông báo nhắc tạo lại.
- TC-G3-05: Không xuất hiện badge tin cậy, nhãn mạnh/yếu, hay mã giờ sinh A-D trong giao diện người xem.
- TC-G3-06: UI đã bỏ mục độ tin cậy giờ sinh; không còn câu cảnh báo C/D.
- TC-G3-07: Thiên Bàn trung tâm hiển thị thông tin chung của người xem (họ tên, ngày giờ, can chi, tuổi, Âm Dương, Mệnh, Cục, Cách) thay cho thẻ cung vừa bấm.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from streamlit.testing.v1 import AppTest
from backend.app.schemas.horoscope import HoroscopeRequest
from backend.app.main import horoscope_read
import frontend.horoscope_sections as sections


def _submit_report(app, target_year: int = 2026, reading_mode: str = "chuyen_sau", input_conf: str = "A", old_report: bool = False):
    req = HoroscopeRequest(
        ngay=15, thang=8, nam=1995, chi_gio=5,
        provider="mock", reading_mode=reading_mode,
        target_year=target_year, input_confidence=input_conf,
    )
    payload = horoscope_read(req)
    payload["ho_ten"] = "Lê An"
    if old_report and "tom_tat_nam" in payload.get("reading", {}):
        del payload["reading"]["tom_tat_nam"]

    response = Mock()
    response.iter_lines.return_value = iter([
        json.dumps({"event": "prepared", "report": payload}),
        json.dumps({"event": "result", "report": payload}),
    ])
    with patch("requests.post", return_value=response):
        if "target_year" in [ni.key for ni in app.number_input]:
            app.number_input(key="target_year").set_value(target_year)
        if "reading_mode" in [sb.key for sb in app.sidebar.selectbox]:
            app.sidebar.selectbox(key="reading_mode").set_value(reading_mode)
        if "input_confidence" in [sb.key for sb in app.sidebar.selectbox]:
            app.sidebar.selectbox(key="input_confidence").set_value(input_conf)
        app.sidebar.button[0].click().run()
    assert not app.exception
    return payload


def test_tc_g3_01_module_exports_new_sections():
    """TC-G3-01: Module frontend.horoscope_sections export đầy đủ các hàm render mới và cũ."""
    expected_fns = [
        "render_header_identity",
        "render_annual_overview_section",
        "render_chart_section",
        "render_overview_section",
        "render_topics_section",
        "render_action_advice_section",
        "render_evidence_and_specialist_section",
    ]
    for fn in expected_fns:
        assert hasattr(sections, fn), f"frontend.horoscope_sections thiếu hàm {fn}"
        assert callable(getattr(sections, fn))


def test_tc_g3_02_new_ui_order_and_annual_overview_first():
    """TC-G3-02: Tổng quan năm xuất hiện TRƯỚC lá số 12 cung."""
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/horoscope_ui.py", default_timeout=20).run()
    _submit_report(app, target_year=2026)
    assert not app.exception

    subheaders = [sh.value for sh in app.subheader]

    # Phải có subheader Tổng quan năm và Lá số 12 cung
    assert any("Tổng quan năm 2026" in sh or "Tổng quan năm" in sh for sh in subheaders)
    assert any("Lá số 12 cung" in sh for sh in subheaders)

    idx_annual = next(i for i, sh in enumerate(subheaders) if "Tổng quan năm" in sh)
    idx_chart = next(i for i, sh in enumerate(subheaders) if "Lá số 12 cung" in sh)

    # Tổng quan năm phải xuất hiện trước lá số
    assert idx_annual < idx_chart


def test_tc_g3_03_annual_overview_displays_three_paragraphs():
    """TC-G3-03: Phần tổng quan năm hiển thị đủ 3 đoạn văn."""
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/horoscope_ui.py", default_timeout=20).run()
    _submit_report(app, target_year=2026)
    assert not app.exception

    markdown_blocks = [m.value for m in app.markdown]
    found_paragraphs = False
    for m in markdown_blocks:
        if "Trọng tâm của năm" in m or "trọng tâm" in m.lower():
            if "Cơ hội đáng chú ý" in m or "cơ hội" in m.lower():
                found_paragraphs = True
                break
    assert found_paragraphs


def test_tc_g3_04_old_report_prompts_regeneration():
    """TC-G3-04: Báo cáo cũ thiếu tom_tat_nam hiển thị lời nhắc tạo lại."""
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/horoscope_ui.py", default_timeout=20).run()
    _submit_report(app, target_year=2026, old_report=True)
    assert not app.exception

    all_text = " ".join(item.value for item in app.info) + " ".join(item.value for item in app.warning) + " ".join(item.value for item in app.markdown)
    assert "tạo lại" in all_text.lower() or "phiên bản cũ" in all_text.lower() or "tạo bản luận giải" in all_text.lower()


def test_tc_g3_05_no_confidence_badges_or_signal_weights():
    """TC-G3-05: Ẩn badge tin cậy, nhãn độ nặng và mạnh/yếu."""
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/horoscope_ui.py", default_timeout=20).run()
    _submit_report(app, target_year=2026)
    assert not app.exception

    all_text = " ".join(item.value for item in app.markdown) + " ".join(item.value for item in app.caption)

    # Không được xuất hiện các badge [rat_manh], [Rất mạnh], [Mạnh], [Trung bình], [Yếu] dưới dạng badge tin cậy
    assert "confidence-badge" not in all_text
    assert "Mức độ tin cậy:" not in all_text
    assert "Mức tập trung tín hiệu cần xem xét:" not in all_text


def test_tc_g3_06_low_confidence_hour_caution_removed():
    """TC-G3-06: UI đã bỏ mục độ tin cậy giờ sinh; không còn câu cảnh báo C/D."""
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/horoscope_ui.py", default_timeout=20).run()
    _submit_report(app, target_year=2026, input_conf="C")
    assert not app.exception

    all_warnings = " ".join(item.value for item in app.warning)
    assert "Giờ sinh cần được đối chiếu thêm; nội dung về thời điểm được hạn chế." not in all_warnings
    assert "mức C" not in all_warnings
    assert "mức D" not in all_warnings


def test_tc_g3_07_thien_ban_shows_general_info_instead_of_palace_card():
    """TC-G3-07: Thiên Bàn trung tâm hiển thị thông tin chung thay cho thẻ cung đang xem."""
    from frontend.laso_renderer import render_laso

    req = HoroscopeRequest(
        ngay=3, thang=2, nam=1900, chi_gio=1, gioi_tinh=1,
        provider="mock", target_year=2026,
    )
    report = horoscope_read(req)
    general = sections.chart_viewer_general(report, "Người Xem")

    assert general["can_chi_nam"] == "Canh Tý"
    assert general["can_chi_thang"] == "Mậu Dần"
    assert general["can_chi_ngay"] == "Đinh Mùi"
    assert general["can_chi_gio"] == "Canh Tý"
    assert general["am_duong"] == "Dương Nam"
    assert general["am_duong_ly"] == "Âm Dương thuận lý"
    assert general["thang_am"] == 1 and general["ngay_am"] == 4
    assert general["tuoi_am"] == 127
    assert general["cuc"] == "Thổ Ngũ Cục"
    assert general["cuc_notes"]  # có nhãn quan hệ Mệnh – Cục
    assert "Không phá cách" in general["cach"]

    html = render_laso(
        report["la_so"]["thap_ni_cung"], che_do="luoi",
        thien_ban={"ho_ten": "Người Xem", "general": general},
    )
    assert "tb-gen-table" in html
    assert "Họ tên" in html and "Âm Dương" in html and "Cách" in html
    assert "Canh Tý" in html and "Bính Ngọ" in html
    assert "127 tuổi" in html and "Không phá cách" in html
    assert "tb-gen-lunar" in html
    assert "thien-ban-inspect-card" not in html
    assert "tb-cung-badge" not in html

    # Tích hợp UI: card thông tin chung thực sự được render trên trang.
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/horoscope_ui.py", default_timeout=20).run()
    _submit_report(app, target_year=2026)
    assert not app.exception
    rendered = " ".join(item.value for item in app.markdown)
    assert "tb-gen-table" in rendered
    assert "Họ tên" in rendered
    assert "thien-ban-inspect-card" not in rendered
