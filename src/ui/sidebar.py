"""
サイドバー：言語・CEDXM読み込み・板サイズ・実行ボタン
"""
import streamlit as st
from src.i18n import LANGUAGES, get_text
from src.input import load_demo_project
from src.cedxm import load_cedxm, create_board_from_height
from src.masterdata import default_master


def render_sidebar():
    """サイドバーを描画し、実行ボタンが押された場合 True を返す。"""
    current_lang = st.session_state.language

    st.subheader(get_text("language_selection", current_lang))
    selected_language = st.selectbox(
        "言語 / Language",
        options=list(LANGUAGES.keys()),
        index=list(LANGUAGES.values()).index(current_lang),
        key="language_selector",
        label_visibility="collapsed"
    )
    if LANGUAGES[selected_language] != current_lang:
        st.session_state.language = LANGUAGES[selected_language]
        st.rerun()

    st.divider()
    st.subheader(get_text("load_cedxm", current_lang))
    cedxm_upload_key = st.session_state.get("cedxm_upload_key", 0)
    cedxm_file = st.file_uploader(
        get_text("load_cedxm", current_lang),
        type=["cedxm", "xml"],
        accept_multiple_files=False,
        key=f"cedxm_uploader_{cedxm_upload_key}",
        label_visibility="collapsed"
    )
    if cedxm_file is not None:
        try:
            content = cedxm_file.getvalue().decode("utf-8-sig")
            proj = load_cedxm(content)
            st.session_state.project = proj
            st.session_state.board = create_board_from_height(proj.room.height)
            if "rules" not in st.session_state or "output_mode" not in st.session_state:
                _b, _r, _mode = default_master()
                if "rules" not in st.session_state:
                    st.session_state.rules = _r
                if "output_mode" not in st.session_state:
                    st.session_state.output_mode = _mode
            st.session_state.results = {
                "panels": [], "errors": [], "placements": [],
                "utilization": 0.0, "num_sheets": 0, "alloc_time": 0.0
            }
            st.session_state.extra_walls = []
            if "structural_system" in st.session_state:
                del st.session_state["structural_system"]
            st.session_state.cedxm_upload_key = cedxm_upload_key + 1
            st.success(get_text("load_cedxm_success", current_lang))
            st.rerun()
        except Exception as e:
            st.error(f"CEDXM読み込みエラー: {e}")

    st.divider()
    st.subheader(get_text("board_size_selection", current_lang))
    BOARD_OPTIONS = [
        ("3×8 (910×2430mm)", 910, 2430),
        ("3×9 (910×2730mm)", 910, 2730),
        ("3×10 (910×3030mm)", 910, 3030),
    ]
    b_curr = st.session_state.board
    board_index = 0
    for i, (_, w, h) in enumerate(BOARD_OPTIONS):
        if (b_curr.raw_width, b_curr.raw_height) == (w, h):
            board_index = i
            break
    selected_board_label = st.selectbox(
        get_text("standard_board_size", current_lang),
        options=[opt[0] for opt in BOARD_OPTIONS],
        index=board_index,
        key=f"sidebar_board_size_{cedxm_upload_key}",
        label_visibility="collapsed"
    )
    for label, w, h in BOARD_OPTIONS:
        if label == selected_board_label:
            if b_curr.raw_width != w or b_curr.raw_height != h:
                st.session_state.board.raw_width = w
                st.session_state.board.raw_height = h
                st.session_state.board.name = f"GB-R {label.split()[0]}"
            break

    st.divider()
    st.header(get_text("execute_button", current_lang))
    st.divider()
    run = st.button(get_text("execute_button", current_lang), type="primary", use_container_width=True)
    if run:
        st.write(f"{get_text('execution_params', current_lang)}")
        st.write(f"- {get_text('standard_board_size', current_lang)}: {st.session_state.board.name}")
    st.divider()
    st.info("詳細な設定は「6. 設定」タブで変更できます。")
    return run
