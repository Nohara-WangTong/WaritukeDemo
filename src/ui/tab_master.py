"""
5. マスター内容ビュー
"""
from dataclasses import asdict
import streamlit as st
from src.i18n import get_text


def render_tab_master(board, rules, output_mode):
    current_lang = st.session_state.language
    st.subheader(get_text("current_master", current_lang))
    st.json({
        "board": asdict(board),
        "rules": asdict(rules),
        "output_mode": output_mode
    })
