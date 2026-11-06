"""Tests for KMS Tu Vi UI Foundation, Font Payload, Theme & Fixture.

Verifies:
1. Font subset woff2 files exist (weights 400 & 600 only, no 500/700).
2. Base64 font payload size <= 70 KB (71,680 bytes).
3. 100% offline capability (no external HTTP/HTTPS/CDN references).
4. Completeness of :root CSS tokens matching .taste-skill/direction.json.
5. Legacy CSS files (horoscope.css, research.css) are removed.
6. Fixture mode toggling via KMS_UI_FIXTURE and fixture payloads.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import pytest

from frontend.ui_themes import (
    get_font_base64,
    get_theme_css,
    get_theme_tokens,
    FONTS_DIR,
    APP_CSS_PATH,
    DIRECTION_JSON_PATH,
)
from frontend.ui_fixture import (
    is_fixture_mode,
    load_fixture,
    mock_reading_events,
    mock_ask_horoscope,
    mock_stats,
    mock_search,
    mock_dossier,
)

ROOT_DIR = Path(__file__).resolve().parent.parent


def test_font_files_exist_and_weights():
    """Confirms plex-400.woff2 and plex-600.woff2 exist, and no 500/700 woff2 exists."""
    font_400 = FONTS_DIR / "plex-400.woff2"
    font_600 = FONTS_DIR / "plex-600.woff2"
    font_500 = FONTS_DIR / "plex-500.woff2"
    font_700 = FONTS_DIR / "plex-700.woff2"

    assert font_400.exists(), f"plex-400.woff2 missing at {font_400}"
    assert font_600.exists(), f"plex-600.woff2 missing at {font_600}"
    assert not font_500.exists(), "plex-500.woff2 must not exist (only 400 and 600 permitted)"
    assert not font_700.exists(), "plex-700.woff2 must not exist (only 400 and 600 permitted)"

    # Base64 loader works for 400 and 600
    b64_400 = get_font_base64(400)
    b64_600 = get_font_base64(600)
    assert len(b64_400) > 0
    assert len(b64_600) > 0

    with pytest.raises(FileNotFoundError):
        get_font_base64(500)


def test_base64_font_payload_size():
    """Verifies that combined base64 woff2 font payload is <= 70 KB (71,680 bytes)."""
    b64_400 = get_font_base64(400)
    b64_600 = get_font_base64(600)
    total_bytes = len(b64_400) + len(b64_600)
    max_allowed = 70 * 1024  # 71,680 bytes

    assert total_bytes <= max_allowed, (
        f"Font payload exceeds budget: {total_bytes:,} bytes "
        f"({total_bytes / 1024:.2f} KB) > {max_allowed:,} bytes (70 KB)"
    )
    # Check individual weights are balanced (around 24-28 KB each)
    assert 10 * 1024 < len(b64_400) < 35 * 1024
    assert 10 * 1024 < len(b64_600) < 35 * 1024


def test_offline_no_external_urls():
    """Asserts that the theme CSS contains NO external URLs (100% offline)."""
    css = get_theme_css()
    raw_app_css = APP_CSS_PATH.read_text(encoding="utf-8")

    # Banned URL patterns: http://, https://, protocol-relative url(//...), external font/CDN services, @import
    banned_pattern = re.compile(
        r"(https?:|fonts\.googleapis\.com|fonts\.gstatic\.com|cdnjs|unpkg|@import)",
        re.IGNORECASE,
    )
    matches_in_theme = banned_pattern.findall(css)
    assert not matches_in_theme, f"Found external URL references in theme CSS: {matches_in_theme}"

    matches_in_app = banned_pattern.findall(raw_app_css)
    assert not matches_in_app, f"Found external URL references in app.css: {matches_in_app}"

    # Check all url(...) calls in CSS - must ONLY be data:font/woff2;base64,
    url_pattern = re.compile(r"url\s*\(\s*['\"]?([^'\")]+)['\"]?\s*\)", re.IGNORECASE)
    urls = url_pattern.findall(css)
    assert urls, "Theme CSS should contain font url() declarations"
    for u in urls:
        assert u.startswith("data:font/woff2;base64,"), f"Forbidden non-offline URL: {u[:50]}"


def test_tokens_completeness():
    """Verifies all locked tokens from .taste-skill/direction.json are present and match."""
    direction = json.loads(DIRECTION_JSON_PATH.read_text(encoding="utf-8"))
    locked_tokens = direction["style"]["tokens"]

    tokens = get_theme_tokens()
    assert tokens["ground"] == locked_tokens["ground"] == "#f9fbfc"
    assert tokens["surface"] == locked_tokens["surface"] == "#ffffff"
    assert tokens["raised"] == locked_tokens["raised"] == "#f4f6f8"
    assert tokens["active"] == locked_tokens["active"] == "#ebedee"
    assert tokens["border"] == locked_tokens["border"] == "#e8eaec"
    assert tokens["rule"] == locked_tokens["rule"] == "#f0f1f2"
    assert tokens["control"] == locked_tokens["control"] == "#cdced1"
    assert tokens["text"] == locked_tokens["text"] == "#131416"
    assert tokens["muted"] == locked_tokens["muted"] == "#5d5f60"
    assert tokens["accent"] == locked_tokens["accent"] == "#1b6c80"
    assert tokens["positive"] == locked_tokens["positive"] == "#1e7b4f"
    assert tokens["negative"] == locked_tokens["negative"] == "#c4242a"
    assert tokens["warning"] == locked_tokens["warning"] == "#92400e"
    assert tokens["chart"] == locked_tokens["chart"]
    assert tokens["radius"]["sheet"] == 16
    assert tokens["radius"]["card"] == 8
    assert tokens["radius"]["control"] == 6

    # Verify CSS variables in app.css
    css = APP_CSS_PATH.read_text(encoding="utf-8")
    for key, val in [
        ("--ground", "#f9fbfc"),
        ("--surface", "#ffffff"),
        ("--raised", "#f4f6f8"),
        ("--active", "#ebedee"),
        ("--border", "#e8eaec"),
        ("--rule", "#f0f1f2"),
        ("--control", "#cdced1"),
        ("--text", "#131416"),
        ("--muted", "#5d5f60"),
        ("--accent", "#1b6c80"),
        ("--positive", "#1e7b4f"),
        ("--negative", "#c4242a"),
        ("--warning", "#92400e"),
        ("--radius-sheet", "16px"),
        ("--radius-card", "8px"),
        ("--radius-control", "6px"),
        ("--sheet-inset", "8px"),
        ("--sidebar-width", "228px"),
    ]:
        pattern = rf"{key}\s*:\s*{val}"
        assert re.search(pattern, css), f"Missing token definition in app.css: {key}: {val}"


def test_legacy_css_removed():
    """Confirms legacy CSS files horoscope.css and research.css are deleted."""
    legacy_horoscope = ROOT_DIR / "frontend" / "assets" / "horoscope.css"
    legacy_research = ROOT_DIR / "frontend" / "assets" / "research.css"

    assert not legacy_horoscope.exists(), f"Legacy file must be removed: {legacy_horoscope}"
    assert not legacy_research.exists(), f"Legacy file must be removed: {legacy_research}"


def test_fixture_mode_toggle(monkeypatch):
    """Verifies KMS_UI_FIXTURE environment toggle and fixture loaders."""
    monkeypatch.delenv("KMS_UI_FIXTURE", raising=False)
    assert not is_fixture_mode()

    monkeypatch.setenv("KMS_UI_FIXTURE", "0")
    assert not is_fixture_mode()

    monkeypatch.setenv("KMS_UI_FIXTURE", "1")
    assert is_fixture_mode()

    # Test loading all fixtures
    report = load_fixture("sample_report")
    assert report.get("status") == "ok"
    assert "reading" in report

    search_data = load_fixture("sample_search")
    assert "results" in search_data or "hits" in search_data or "citations" in search_data

    stats_data = load_fixture("sample_stats")
    assert stats_data.get("status") == "ok"
    assert "total_records" in stats_data

    dossier_data = load_fixture("sample_dossier")
    assert dossier_data.get("name") == "Tử Vi"
    assert len(dossier_data.get("slots", {})) == 14

    ask_data = load_fixture("sample_ask")
    assert ask_data.get("status") == "ok"

    # Test helper mock functions
    assert mock_stats().get("status") == "ok"
    assert mock_search("Cự Môn").get("query") == "Cự Môn"
    assert mock_dossier("Thiên Phủ").get("name") == "Thiên Phủ"
    assert mock_ask_horoscope({"question": "Test"}).get("question") == "Test"

    # Test mock_reading_events
    events = list(mock_reading_events({"ho_ten": "Lê Văn Thử Nghiệm"}))
    assert len(events) == 4
    assert events[0]["event"] == "progress"
    assert events[1]["event"] == "chart_ready"
    assert events[2]["event"] == "prepared"
    assert events[3]["event"] == "result"
    assert events[3]["report"]["ho_ten"] == "Lê Văn Thử Nghiệm"
