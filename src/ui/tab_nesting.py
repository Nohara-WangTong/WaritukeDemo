"""
3. 板取ビュー
"""
import streamlit as st
from src.i18n import get_text
from src.visualization import create_nesting_plotly


def render_tab_nesting(board):
    current_lang = st.session_state.language
    placements = st.session_state.results.get("placements", [])
    util = st.session_state.results.get("utilization", 0.0)

    st.subheader(get_text("nesting_preview", current_lang))
    if placements:
        fig_nesting = create_nesting_plotly(placements, board)
        if fig_nesting:
            st.plotly_chart(fig_nesting, use_container_width=True)
        st.success(f"{get_text('utilization_rate', current_lang)}: {util * 100:.1f}%")
    else:
        st.info(get_text("nesting_info", current_lang))
