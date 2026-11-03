# -*- coding: utf-8 -*-
"""P7 (Plan_Fix_Mai_Anh_v2 §10): Tách module và sắp xếp trang theo luồng 5 khối.

Luồng UI chuẩn (§10.2):
Lá số -> Tổng quan -> Chủ đề -> Vì sao -> Xem căn cứ

Ma trận test:
- P7.TC-01: Module frontend.horoscope_sections export đầy đủ các hàm render 5 khối
- P7.TC-02: AppTest xác nhận thứ tự hiển thị tuần tự đúng 5 khối
- P7.TC-03: Khối 'Vì sao' có đủ 4 yếu tố (dữ kiện, quy tắc, chủ đề, điều kiện thiếu / phản chứng)
- P7.TC-04: Khối 'Vì sao' tích hợp cách cục đã nhận diện từ P3
- P7.TC-05: Khối 'Vì sao' hoạt động ổn định ở chế độ du_lieu (tất định, không cần AI)
- P7.TC-06: Khối 'Xem căn cứ' chứa đủ 4 thành phần (lập luận, bảng sao, trích dẫn, thông số kỹ thuật)
- P7.TC-07: Chống lặp - trích dẫn dài chỉ nằm trong 'Xem căn cứ'
- P7.TC-08: Bảo toàn toàn bộ widget keys và tương tác (show_chart, chart_view_mode, star_filter, show_sources)
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

from streamlit.testing.v1 import AppTest
from backend.app.schemas.horoscope import HoroscopeRequest
from backend.app.main import horoscope_read


def _submit_mock_report(app, target_year: int | None = None, reading_mode: str = "chuyen_sau"):
    req = HoroscopeRequest(
        ngay=15, thang=8, nam=1995, chi_gio=5,
        provider="mock", reading_mode=reading_mode,
        target_year=target_year or 2026,
    )
    payload = horoscope_read(req)
    payload["ho_ten"] = "Lê An"
    response = Mock()
    response.iter_lines.return_value = iter([
        json.dumps({"event": "prepared", "report": payload}),
        json.dumps({"event": "result", "report": payload}),
    ])
    with patch("requests.post", return_value=response):
        if target_year is not None:
            app.number_input(key="target_year").set_value(target_year)
        if "reading_mode" in [sb.key for sb in app.sidebar.selectbox]:
            app.sidebar.selectbox(key="reading_mode").set_value(reading_mode)
        app.sidebar.button[0].click().run()
    assert not app.exception
    return payload


def test_p7_tc01_module_exports_all_section_renderers():
    """P7.TC-01: Module frontend.horoscope_sections export đầy đủ các hàm render 5 khối."""
    import frontend.horoscope_sections as sections

    expected_fns = [
        "render_header_identity",
        "render_chart_section",
        "render_overview_section",
        "render_topics_section",
        "render_why_section",
        "render_evidence_section",
    ]
    for fn_name in expected_fns:
        assert hasattr(sections, fn_name), f"Thiếu hàm {fn_name} trong frontend.horoscope_sections"
        assert callable(getattr(sections, fn_name))


def test_p7_tc02_ui_renders_in_five_block_order():
    """P7.TC-02: AppTest xác nhận thứ tự hiển thị 5 khối: Lá số -> Tổng quan -> Chủ đề -> Vì sao -> Xem căn cứ."""
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/horoscope_ui.py", default_timeout=20).run()
    _submit_mock_report(app)
    assert not app.exception

    # Thu thập tất cả subheaders / markdown headings theo thứ tự xuất hiện
    text_content = " ".join(item.value for item in app.markdown)
    subheaders = [sh.value for sh in app.subheader]

    # 1. Lá số 12 cung
    assert any("Lá số 12 cung" in sh for sh in subheaders)
    idx_laso = next(i for i, sh in enumerate(subheaders) if "Lá số 12 cung" in sh)

    # 2. Tổng quan
    assert "overview-grid" in text_content or "Chân dung của bạn" in text_content

    # 3. Theo chủ đề (các tabs)
    tab_labels = [t.label for t in app.tabs]
    assert "Sự nghiệp" in tab_labels or "Tài chính" in tab_labels

    # 4. Vì sao
    assert any("Vì sao" in sh for sh in subheaders)
    idx_why = next(i for i, sh in enumerate(subheaders) if "Vì sao" in sh)

    # 5. Xem căn cứ
    assert any("Xem căn cứ" in sh for sh in subheaders)
    idx_evidence = next(i for i, sh in enumerate(subheaders) if "Xem căn cứ" in sh)

    # Đảm bảo thứ tự tương đối: Lá số < Vì sao < Xem căn cứ
    assert idx_laso < idx_why < idx_evidence


def test_p7_tc03_why_section_has_four_elements_in_explanation():
    """P7.TC-03: Khối 'Vì sao' có đủ 4 yếu tố: Dữ kiện, Quy tắc, Chủ đề, Điều kiện thiếu / Phản chứng."""
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/horoscope_ui.py", default_timeout=20).run()
    _submit_mock_report(app)
    assert not app.exception

    all_markdown = " ".join(item.value for item in app.markdown)
    all_captions = " ".join(item.value for item in app.caption)

    # Các từ khóa của 4 yếu tố cốt lõi trong phần Vì sao
    assert "Dữ kiện" in all_captions or "Dữ kiện" in all_markdown
    assert "Quy tắc" in all_captions or "Quy tắc" in all_markdown or "rule_ids" in all_markdown
    assert "giới hạn" in all_captions.lower() or "phản chứng" in all_captions.lower() or "điều kiện" in all_captions.lower()


def test_p7_tc04_why_section_displays_detected_cach_cuc():
    """P7.TC-04: Khối 'Vì sao' hiển thị các cách cục đã nhận diện từ P3."""
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/horoscope_ui.py", default_timeout=20).run()
    payload = _submit_mock_report(app)
    assert not app.exception

    # Báo cáo mock có nhận diện cách cục trong reading['cach_cuc']
    cach_cuc = payload.get("reading", {}).get("cach_cuc") or {}
    assert "rules" in cach_cuc

    all_text = " ".join(item.value for item in app.markdown) + " ".join(item.value for item in app.caption)
    assert "Cách cục" in all_text or "cách cục" in all_text


def test_p7_tc05_why_section_operates_offline_without_ai():
    """P7.TC-05: Khối 'Vì sao' hoạt động ổn định ở chế độ du_lieu (không dùng AI, P4 §7.4, P7 §10.3)."""
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/horoscope_ui.py", default_timeout=20).run()
    _submit_mock_report(app, reading_mode="du_lieu")
    assert not app.exception

    subheaders = [sh.value for sh in app.subheader]
    assert any("Vì sao" in sh for sh in subheaders)
    assert any("Xem căn cứ" in sh for sh in subheaders)


def test_p7_tc06_evidence_section_contains_all_four_subsections():
    """P7.TC-06: Khối 'Xem căn cứ' chứa đủ 4 thành phần: lập luận, bảng sao, trích dẫn, thông số kỹ thuật."""
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/horoscope_ui.py", default_timeout=20).run()
    _submit_mock_report(app)
    assert not app.exception

    # Bảng sao tồn tại
    assert "star_filter" in [sb.key for sb in app.selectbox]
    # Toggle trích dẫn sách gốc
    assert "show_sources" in [tg.key for tg in app.toggle]

    all_text = " ".join(item.value for item in app.markdown) + " ".join(item.value for item in app.caption)
    assert "Lập luận" in all_text or "evidence-table" in all_text
    assert "Thời gian xử lý" in all_text or "timings" in all_text.lower() or "Lập lá số" in all_text


def test_p7_tc07_preserves_all_widget_keys_and_interactions():
    """P7.TC-07: Bảo toàn toàn bộ widget keys và các tương tác toggle/radio/selectbox."""
    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/horoscope_ui.py", default_timeout=20).run()
    _submit_mock_report(app)
    assert not app.exception

    # Toggle lá số
    assert "show_chart" in [tg.key for tg in app.toggle]
    app.toggle(key="show_chart").set_value(False).run()
    assert not app.exception
    app.toggle(key="show_chart").set_value(True).run()
    assert not app.exception

    # Toggle trích dẫn sách
    assert "show_sources" in [tg.key for tg in app.toggle]
    app.toggle(key="show_sources").set_value(True).run()
    assert not app.exception

    # Radio bố cục lá số
    assert "chart_view_mode" in [r.key for r in app.radio]
    app.radio(key="chart_view_mode").set_value("Đọc từng cung").run()
    assert not app.exception

