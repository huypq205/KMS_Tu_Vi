"""KMS Tử Vi — Central Theme & Design Token Management.

Provides cached inline font-face declarations (woff2 base64) and unified
app.css stylesheet injection for Streamlit screens.
"""

from __future__ import annotations

import base64
import functools
import json
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "frontend" / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
APP_CSS_PATH = ASSETS_DIR / "app.css"
DIRECTION_JSON_PATH = ROOT_DIR / ".taste-skill" / "direction.json"


@functools.lru_cache(maxsize=4)
def get_font_base64(weight: int) -> str:
    """Reads and base64-encodes a subsetted woff2 font file."""
    font_file = FONTS_DIR / f"plex-{weight}.woff2"
    if not font_file.exists():
        raise FileNotFoundError(
            f"Font file not found: {font_file}. Run scripts/build_fonts.py first."
        )
    return base64.b64encode(font_file.read_bytes()).decode("ascii")


@functools.lru_cache(maxsize=1)
def get_theme_css() -> str:
    """Returns complete inline CSS including @font-face rules and app.css content.

    Only 400 and 600 weights are used (no 500 or 700). Completely offline
    with data: URIs and no external network calls.
    """
    b64_400 = get_font_base64(400)
    b64_600 = get_font_base64(600)

    font_faces = (
        f"@font-face {{"
        f"font-family: 'IBM Plex Sans';"
        f"font-weight: 400;"
        f"font-style: normal;"
        f"font-display: swap;"
        f"src: url('data:font/woff2;base64,{b64_400}') format('woff2');"
        f"}}\n"
        f"@font-face {{"
        f"font-family: 'IBM Plex Sans';"
        f"font-weight: 600;"
        f"font-style: normal;"
        f"font-display: swap;"
        f"src: url('data:font/woff2;base64,{b64_600}') format('woff2');"
        f"}}\n"
    )

    if not APP_CSS_PATH.exists():
        raise FileNotFoundError(f"Stylesheet not found: {APP_CSS_PATH}")

    app_css = APP_CSS_PATH.read_text(encoding="utf-8")
    return font_faces + app_css


@functools.lru_cache(maxsize=1)
def get_theme_tokens() -> dict[str, Any]:
    """Returns official design tokens dictionary locked from .taste-skill/direction.json."""
    if DIRECTION_JSON_PATH.exists():
        try:
            data = json.loads(DIRECTION_JSON_PATH.read_text(encoding="utf-8"))
            tokens = data.get("style", {}).get("tokens")
            if tokens:
                return dict(tokens)
        except Exception:
            pass

    # Fallback to locked canonical tokens
    return {
        "ground": "#f9fbfc",
        "surface": "#ffffff",
        "raised": "#f4f6f8",
        "active": "#ebedee",
        "border": "#e8eaec",
        "rule": "#f0f1f2",
        "control": "#cdced1",
        "text": "#131416",
        "muted": "#5d5f60",
        "accent": "#1b6c80",
        "positive": "#1e7b4f",
        "negative": "#c4242a",
        "warning": "#92400e",
        "chart": ["#1b6c80", "#2f70bb", "#a86f0c"],
        "pills": {
            "positive": ["#dcfae5", "#04250e"],
            "negative": ["#ffedea", "#831c1e"],
            "warning": ["#fffbeb", "#92400e"],
            "neutral": ["#ebedee", "#353736"],
        },
        "radius": {"card": 8, "control": 6, "sheet": 16},
        "sheetInset": 8,
        "density": "medium",
        "rowHeight": 48,
        "sidebarWidth": 228,
        "gap": 24,
        "pad": 24,
        "controlHeight": 32,
    }


def apply_theme(title: str | None = None) -> None:
    """Injects font-face definitions and unified app.css into the active Streamlit app.

    Optionally sets a page title if provided.
    """
    import streamlit as st

    css = get_theme_css()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    if title:
        st.title(title)
