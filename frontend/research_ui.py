"""Shared plain research surface using the unified KMS theme and typography."""
from __future__ import annotations

from pathlib import Path
import streamlit as st
from frontend.ui_themes import apply_theme

ROOT = Path(__file__).resolve().parents[1]


def setup(title: str) -> None:
    """Sets page configuration and injects unified offline theme (app.css + woff2)."""
    try:
        st.set_page_config(
            page_title=f"{title} · KMS Tử Vi",
            layout="wide",
            initial_sidebar_state="auto",
        )
    except Exception:
        # Avoid duplicate set_page_config if already executed in multipage navigation
        pass

    apply_theme()
    st.title(title)
    st.caption("KMS Tử Vi · Tra cứu và kiểm chứng theo từng nguồn")
