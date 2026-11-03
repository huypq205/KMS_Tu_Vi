"""Shared plain research surface using the existing KMS typography and palette."""
import base64
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]


def setup(title):
    st.set_page_config(page_title=title+' · KMS Tử Vi', layout='wide', initial_sidebar_state='auto')
    fonts = ''
    for weight in (400,500,600):
        encoded = base64.b64encode((ROOT/f'frontend/assets/fonts/IBMPlexSans-{weight}.ttf').read_bytes()).decode('ascii')
        fonts += f"@font-face{{font-family:'IBM Plex Sans';font-weight:{weight};src:url(data:font/ttf;base64,{encoded}) format('truetype');}}"
    style = (ROOT/'frontend/assets/horoscope.css').read_text(encoding='utf-8')
    st.markdown('<style>'+fonts+style+(ROOT/'frontend/assets/research.css').read_text(encoding='utf-8')+'</style>', unsafe_allow_html=True)
    st.title(title)
    st.caption('KMS Tử Vi · Tra cứu và kiểm chứng theo từng nguồn')
