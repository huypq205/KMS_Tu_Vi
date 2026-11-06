"""Milestone M3 Empirical Stress Testing & Challenger Suite.

Adversarially tests Streamlit UIs across:
- frontend/star_dossier_ui.py
- frontend/case_validation_ui.py
- frontend/app.py

Validates both live and fixture mode (KMS_UI_FIXTURE=1), widget key preservation,
error resilience under network / API failures, empty state handling, and 0-emoji rules.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import re
from unittest.mock import MagicMock, patch

import pytest
from streamlit.testing.v1 import AppTest

from backend.app.services.star_dossier import get_star_dossier

ROOT = Path(__file__).resolve().parents[1]
EMOJI_PATTERN = re.compile(r"[\U0001F300-\U0001FAFF\u2700-\u27BF\u2600-\u26FF]")


# ==============================================================================
# 1. STAR DOSSIER UI STRESS TESTS
# ==============================================================================

def test_star_dossier_fixture_mode_full_flow():
    """Stress-test star_dossier_ui in KMS_UI_FIXTURE=1 mode."""
    with patch.dict(os.environ, {"KMS_UI_FIXTURE": "1"}):
        ui = AppTest.from_file(str(ROOT / "frontend/star_dossier_ui.py"), default_timeout=25).run()
        assert not ui.exception

        # Verify essential title and setup
        assert any("Hồ sơ sao" in t.value for t in ui.title)

        # Check widget key preservation
        assert ui.selectbox(key="dossier_star") is not None
        assert ui.checkbox(key="dossier_seeds") is not None
        assert ui.button(key="load_dossier") is not None

        # In fixture mode, auto-loads sample dossier on first visit
        assert "dossier_result" in ui.session_state
        assert ui.session_state["dossier_result"]["name"] in {"Tử Vi", "Vũ Khúc"}

        # Check 4 structured markdown headings
        headings = [h.value for h in ui.markdown if h.value.startswith("### ")]
        assert "### Tiếng nói từng sách và trang dẫn" in headings
        assert "### Bản chất, Âm dương và Biểu hiện" in headings
        assert "### Tổ hợp sao, Tứ Hóa và Sát tinh" in headings
        assert "### Ca nghiệm lý thực tế" in headings

        # Check book badges are present
        all_markdown = " ".join(m.value for m in ui.markdown)
        assert "book-badge" in all_markdown
        assert "book-npl" in all_markdown

        # Simulate user changing selectbox and clicking Tra cứu
        ui.selectbox(key="dossier_star").select("Thái Dương")
        ui.button(key="load_dossier").click().run()
        assert not ui.exception
        assert ui.session_state["dossier_result"]["name"] == "Thái Dương"


def test_star_dossier_live_mode_and_resilience():
    """Stress-test star_dossier_ui under API errors, corrupt JSON, and live success."""
    with patch.dict(os.environ, {"KMS_UI_FIXTURE": "0"}):
        # 1. Initial screen without fixture mode: should show info message
        ui = AppTest.from_file(str(ROOT / "frontend/star_dossier_ui.py"), default_timeout=25).run()
        assert not ui.exception
        assert any("Chọn một sao" in inf.value for inf in ui.info)

        # 2. Network error on load_dossier: must show st.error and not crash AppTest
        with patch("frontend.research_transport.api_get", side_effect=ConnectionError("Failed to reach KMS backend")):
            ui.button(key="load_dossier").click().run()
        assert not ui.exception
        assert any("Chưa tải được hồ sơ sao" in err.value for err in ui.error)

        # 3. Corrupt response (missing 14 slots): must show st.error and not crash
        with patch("frontend.research_transport.api_get", return_value={"name": "Tử Vi", "slots": {"invalid": {}}}):
            ui.button(key="load_dossier").click().run()
        assert not ui.exception
        assert any("Chưa tải được hồ sơ sao" in err.value for err in ui.error)

        # 4. Valid response: renders successfully
        canonical = get_star_dossier("Vũ Khúc")
        with patch("frontend.research_transport.api_get", return_value=canonical):
            ui.button(key="load_dossier").click().run()
        assert not ui.exception
        assert ui.session_state["dossier_result"]["name"] == "Vũ Khúc"
        assert any("Nguồn" in c.value for c in ui.caption)


def test_star_dossier_query_param_direct_navigation():
    """Verify ?star= query parameter directly loads star."""
    with patch.dict(os.environ, {"KMS_UI_FIXTURE": "1"}):
        ui = AppTest.from_file(str(ROOT / "frontend/star_dossier_ui.py"), default_timeout=25)
        ui.query_params["star"] = "Thiên Phủ"
        ui.run()
        assert not ui.exception
        assert ui.session_state["dossier_result"]["name"] == "Thiên Phủ"


# ==============================================================================
# 2. CASE VALIDATION UI STRESS TESTS
# ==============================================================================

def test_case_validation_fixture_mode_full_flow():
    """Stress-test case_validation_ui in KMS_UI_FIXTURE=1 mode."""
    with patch.dict(os.environ, {"KMS_UI_FIXTURE": "1"}):
        ui = AppTest.from_file(str(ROOT / "frontend/case_validation_ui.py"), default_timeout=25).run()
        assert not ui.exception
        assert any("Nhật ký nghiệm lý" in t.value for t in ui.title)

        # Verify preserved keys
        assert ui.text_input(key="journal_case_id") is not None
        assert ui.button(key="journal_open") is not None
        assert ui.selectbox(key="journal_confidence") is not None
        assert ui.button(key="journal_create") is not None
        assert ui.button(key="journal_stats") is not None

        # Test Opening a Case via fixture
        ui.text_input(key="journal_case_id").set_value("TV-2026-FIXTURE")
        ui.button(key="journal_open").click().run()
        assert not ui.exception

        active = ui.session_state.get("journal_case")
        assert active is not None
        assert active["case_id"] == "TV-2026-FIXTURE"
        assert active["input_confidence"] == "A"
        assert len(active["predictions"]) >= 1
        assert len(active["events"]) >= 1

        # Panel 4: Test checking statistics via fixture
        ui.button(key="journal_stats").click().run()
        assert not ui.exception
        assert any("32 ca đã đối chiếu" in c.value for c in ui.caption)
        assert len(ui.table) >= 1  # Result counts table


def test_case_validation_empty_states_and_validation_resilience():
    """Stress-test case_validation_ui empty states and error notices in live mode."""
    with patch.dict(os.environ, {"KMS_UI_FIXTURE": "0"}):
        ui = AppTest.from_file(str(ROOT / "frontend/case_validation_ui.py"), default_timeout=25).run()
        assert not ui.exception

        # Panels 2 and 3 should render empty state cards
        all_md = " ".join(m.value for m in ui.markdown)
        assert "journal-empty-state" in all_md
        assert "Chưa mở hồ sơ ca nghiệm lý" in all_md

        # Click open without entering case id -> error notice
        ui.button(key="journal_open").click().run()
        assert not ui.exception
        assert "Vui lòng nhập mã ca trước khi mở" in " ".join(m.value for m in ui.markdown)

        # Click create without snapshot -> error notice
        ui.button(key="journal_create").click().run()
        assert not ui.exception
        assert "Cần tạo bài đọc hoặc mở bản chụp trước" in " ".join(m.value for m in ui.markdown)


def test_case_validation_backend_transport_error_resilience():
    """Ensure API errors in case_validation_ui render clean notice without crashing."""
    with patch.dict(os.environ, {"KMS_UI_FIXTURE": "0"}):
        ui = AppTest.from_file(str(ROOT / "frontend/case_validation_ui.py"), default_timeout=25).run()
        assert not ui.exception

        with patch("frontend.research_transport.api_get", side_effect=RuntimeError("502 Bad Gateway")):
            ui.text_input(key="journal_case_id").set_value("TV-TEST")
            ui.button(key="journal_open").click().run()

        assert not ui.exception
        all_md = " ".join(m.value for m in ui.markdown)
        assert "notice-error" in all_md
        assert "502 Bad Gateway" in all_md


# ==============================================================================
# 3. KMS MAIN APP UI STRESS TESTS
# ==============================================================================

def test_app_ui_fixture_mode_and_zero_emojis():
    """Stress-test frontend/app.py in fixture mode, checking tabs, badges, Altair, and 0 emojis."""
    with patch.dict(os.environ, {"KMS_UI_FIXTURE": "1"}):
        ui = AppTest.from_file(str(ROOT / "frontend/app.py"), default_timeout=30).run()
        assert not ui.exception

        # Strict 0 emoji assertion on all text elements in the entire app
        all_text_elements = (
            [t.value for t in ui.title]
            + [h.value for h in ui.header]
            + [s.value for s in ui.subheader]
            + [c.value for c in ui.caption]
            + [m.value for m in ui.markdown]
            + [w.value for w in ui.warning]
            + [e.value for e in ui.error]
            + [i.value for i in ui.info]
        )
        for text in all_text_elements:
            emojis = EMOJI_PATTERN.findall(text)
            assert len(emojis) == 0, f"Found forbidden emoji in UI element: {emojis} in '{text[:80]}'"

        # Sidebar health check with fixture
        assert any("DB: 10,456 bản ghi" in s.value for s in ui.success)

        # Tab 1: Search was auto-loaded in fixture mode
        assert "sample_search_loaded" in ui.session_state
        assert "current_search_data" in ui.session_state
        search_data = ui.session_state["current_search_data"]
        assert search_data["status"] == "ok"
        assert len(search_data["results"]) > 0

        # Verify tier badge classes in search results
        search_md = " ".join(m.value for m in ui.markdown)
        assert "tier-badge" in search_md
        assert "tier-t1" in search_md

        # Tab 3: Thống kê metrics
        metric_labels = [m.label for m in ui.metric]
        assert "Tổng bản ghi" in metric_labels
        assert "Chunk đã index" in metric_labels
        assert "Dòng chỉ mục FTS5" in metric_labels

        metric_values = [m.value for m in ui.metric]
        assert "10,456" in metric_values
        assert "4,350" in metric_values

        # Check dataframes
        assert len(ui.dataframe) >= 2


def test_app_ui_chat_ask_fixture_flow():
    """Stress-test Tab 2 (Hỏi đáp RAG) in fixture mode."""
    with patch.dict(os.environ, {"KMS_UI_FIXTURE": "1"}):
        ui = AppTest.from_file(str(ROOT / "frontend/app.py"), default_timeout=30).run()
        assert not ui.exception

        # Locate question text area and "Hỏi" button
        ui.text_area[0].set_value("Sao Thiên Phủ được giải nghĩa thế nào?")
        # Find the "Hỏi" button (second button, first is "Tìm kiếm")
        ask_button = [b for b in ui.button if b.label == "Hỏi"][0]
        ask_button.click().run()
        assert not ui.exception

        # Check answered content and citations
        all_md = " ".join(m.value for m in ui.markdown)
        assert "Thiên Phủ" in all_md
        assert "Nguồn trích dẫn" in " ".join(s.value for s in ui.subheader)
        assert "tier-badge" in all_md


def test_app_ui_live_mode_network_failure_resilience():
    """Stress-test frontend/app.py under complete backend outage in live mode."""
    with patch.dict(os.environ, {"KMS_UI_FIXTURE": "0"}):
        with patch("requests.get", side_effect=Exception("Connection refused (backend down)")):
            ui = AppTest.from_file(str(ROOT / "frontend/app.py"), default_timeout=30).run()

        assert not ui.exception
        # Sidebar should report connection failure gracefully
        assert any("Không kết nối được backend" in err.value for err in ui.error)
        # Stats tab should report error gracefully
        assert any("Không lấy được dữ liệu thống kê" in err.value for err in ui.error)


# ==============================================================================
# 4. CROSS-UI WIDGET KEY INTEGRITY
# ==============================================================================

def test_widget_keys_no_duplicate_collision():
    """Verify that multiple consecutive runs with AppTest do not produce widget collisions."""
    with patch.dict(os.environ, {"KMS_UI_FIXTURE": "1"}):
        # 1. Star Dossier UI multiple runs
        dossier_app = AppTest.from_file(str(ROOT / "frontend/star_dossier_ui.py"), default_timeout=20).run()
        assert not dossier_app.exception
        dossier_app.button(key="load_dossier").click().run()
        assert not dossier_app.exception
        dossier_app.button(key="load_dossier").click().run()
        assert not dossier_app.exception

        # 2. Case Validation UI multiple runs & key uniqueness
        case_app = AppTest.from_file(str(ROOT / "frontend/case_validation_ui.py"), default_timeout=20).run()
        assert not case_app.exception
        case_app.text_input(key="journal_case_id").set_value("TV-001")
        case_app.button(key="journal_open").click().run()
        assert not case_app.exception
        case_app.button(key="journal_stats").click().run()
        assert not case_app.exception



# ==============================================================================
# 5. ADVERSARIAL EDGE CASES & UNIT ORACLES
# ==============================================================================

def test_tier_badge_and_book_badge_oracles():
    """Adversarial stress-testing of badge renderers with malformed inputs."""
    from frontend.app import tier_badge
    from frontend.star_dossier_ui import book_badge_html

    # Null/empty/unexpected inputs to book_badge_html
    assert 'class="book-badge book- badge-book-"' in book_badge_html("")
    assert 'class="book-badge book- badge-book-"' in book_badge_html(None)
    bad_book = book_badge_html("CUSTOM_BOOK", show_full_name=True)
    assert "CUSTOM_BOOK" in bad_book
    assert "book-custom_book" in bad_book

    # Null/empty/unexpected inputs to tier_badge
    t0 = tier_badge(0, None)
    assert "tier-t0" in t0
    assert "Tier 0" in t0

    t9 = tier_badge(9, "Chưa duyệt")
    assert "tier-t9" in t9
    assert "Chưa duyệt" in t9


def test_report_snapshot_oracle_and_ui_handling():
    """Verify report_snapshot validates strict 12-palace schema and UI handles malformed reports."""
    from frontend.case_validation_ui import report_snapshot
    from frontend.ui_fixture import load_fixture

    # 1. Malformed reports must fail ChartSnapshot validation (ValueError/ValidationError)
    with pytest.raises(ValueError):
        report_snapshot({})

    with pytest.raises(ValueError):
        report_snapshot({"palaces": [{"cung_so": 1}]})

    # 2. Valid report from sample_report fixture must pass validation
    sample_report = load_fixture("sample_report")
    snapshot = report_snapshot(sample_report)
    assert len(snapshot["palaces"]) == 12
    assert len(snapshot["facts"]) >= 1
    assert snapshot["tu_hoa_table"] == "lasotuvi"

    # 3. Test UI handles malformed report in session_state gracefully
    with patch.dict(os.environ, {"KMS_UI_FIXTURE": "0"}):
        ui = AppTest.from_file(str(ROOT / "frontend/case_validation_ui.py"), default_timeout=25)
        ui.session_state["report"] = {"invalid_report_structure": True}
        ui.run()
        assert not ui.exception
        all_md = " ".join(m.value for m in ui.markdown)
        assert "Bài đọc hiện tại chưa có snapshot hợp lệ" in all_md

