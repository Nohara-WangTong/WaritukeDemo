"""
4. 図面・帳票ビュー（部材表・板取結果・エラー一覧のダウンロード）
"""
import streamlit as st
from src.i18n import get_text
from src.output import df_panels, df_errors, df_boards


def render_tab_drawings(board):
    current_lang = st.session_state.language
    panels = st.session_state.results.get("panels", [])
    errors = st.session_state.results.get("errors", [])
    placements = st.session_state.results.get("placements", [])
    df_p = df_panels(panels)
    df_e = df_errors(errors)
    df_s = df_boards(placements, board)

    st.subheader(get_text("table_output", current_lang))
    st.write(f"**{get_text('parts_table', current_lang)}**")
    st.dataframe(df_p, use_container_width=True)
    st.download_button(get_text("download_parts", current_lang), data=df_p.to_csv(index=False).encode("utf-8-sig"), file_name="panels.csv", mime="text/csv")

    st.write(f"**{get_text('sheet_layout', current_lang)}**")
    st.dataframe(df_s, use_container_width=True, height=200)
    st.download_button(get_text("download_nesting", current_lang), data=df_s.to_csv(index=False).encode("utf-8-sig"), file_name="nesting.csv", mime="text/csv")

    st.write(f"**{get_text('error_list', current_lang)}**")
    st.dataframe(df_e, use_container_width=True, height=160)
    st.download_button(get_text("download_errors", current_lang), data=df_e.to_csv(index=False).encode("utf-8-sig"), file_name="errors.csv", mime="text/csv")
