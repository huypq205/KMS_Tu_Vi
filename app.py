"""Streamlit entrypoint cho KMS Tu Vi Horoscope."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "vendor") not in sys.path:
    sys.path.insert(0, str(ROOT / "vendor"))

import streamlit as st

st.navigation([
    st.Page('frontend/horoscope_ui.py', title='Luận giải lá số', default=True),
    st.Page('frontend/star_dossier_ui.py', title='Hồ sơ sao', url_path='ho-so-sao'),
]).run()

