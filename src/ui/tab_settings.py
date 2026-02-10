"""
6. 設定タブ（板サイズ・規格・板取ルール）
"""
import streamlit as st
from src.i18n import get_text


def render_tab_settings():
    current_lang = st.session_state.language
    st.subheader(get_text("master_management", current_lang))
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### " + get_text("board_size_selection", current_lang))
        board_options = {
            "3×8 (910×2430mm)": (910, 2430),
            "3×9 (910×2730mm)": (910, 2730),
            "3×10 (910×3030mm)": (910, 3030)
        }
        keys_list = list(board_options.keys())
        b_master = st.session_state.board
        board_settings_index = 0
        for idx, (_, (bw, bh)) in enumerate(board_options.items()):
            if (b_master.raw_width, b_master.raw_height) == (bw, bh):
                board_settings_index = idx
                break
        selected_board_settings = st.selectbox(
            get_text("standard_board_size", current_lang),
            keys_list,
            index=board_settings_index,
            key="board_settings"
        )
        bw_new, bh_new = board_options[selected_board_settings]
        if st.session_state.board.raw_width != bw_new or st.session_state.board.raw_height != bh_new:
            st.session_state.board.raw_width = bw_new
            st.session_state.board.raw_height = bh_new
            st.session_state.board.name = f"GB-R {selected_board_settings.split()[0]}"

        rot_settings = st.checkbox(get_text("allow_rotation", current_lang), value=st.session_state.board.rotatable, key="rot_settings")
        st.session_state.board.rotatable = rot_settings

        st.markdown("### " + get_text("output_format", current_lang))
        output_options = ["真物", "セミ", "フル"] if current_lang == "ja" else ["Good", "Semi", "Full"]
        _mode = st.session_state.output_mode if st.session_state.output_mode != "良物" else "真物"
        current_index = ["真物", "セミ", "フル"].index(_mode)
        output_mode_settings = st.radio(
            "出力形態選択",
            output_options,
            index=current_index,
            horizontal=True,
            key="output_settings",
            label_visibility="collapsed"
        )
        if current_lang != "ja":
            mode_mapping = {"Good": "真物", "Semi": "セミ", "Full": "フル"}
            st.session_state.output_mode = mode_mapping.get(output_mode_settings, output_mode_settings)
        else:
            st.session_state.output_mode = output_mode_settings

    with col2:
        st.markdown("### " + get_text("standards_rules", current_lang))
        st.session_state.rules.min_piece = int(st.number_input(get_text("min_piece", current_lang), value=st.session_state.rules.min_piece, min_value=10, step=10, key="min_piece_settings"))
        st.session_state.rules.clearance = int(st.number_input(get_text("clearance", current_lang), value=st.session_state.rules.clearance, min_value=0, step=1, key="clearance_settings"))
        st.session_state.rules.kerf = int(st.number_input(get_text("blade_thickness", current_lang), value=st.session_state.rules.kerf, min_value=0, step=1, key="kerf_settings"))
        st.session_state.rules.joint = int(st.number_input(get_text("joint_width", current_lang), value=st.session_state.rules.joint, min_value=0, step=1, key="joint_settings"))

        st.markdown("### " + get_text("nesting_heuristics", current_lang))
        prefer_y_long_settings = st.radio(
            get_text("processing_method", current_lang),
            [get_text("yield_priority", current_lang), get_text("length_priority", current_lang)],
            index=0,
            horizontal=False,
            key="prefer_y_settings"
        ) == get_text("length_priority", current_lang)

    st.divider()
    st.info("設定を変更した後は、「▶ 割付・板取を実行」ボタンで再計算してください。")
