"""
2. 割付ビュー（壁立面・間柱設定・自動修正）
"""
import streamlit as st
from src.i18n import get_text
from src.allocating import calculate_corner_winning_rules, allocate_walls_with_architectural_constraints, extra_walls_to_wall_info
from src.visualization import create_wall_elevation_plotly
from src.nesting import simple_nesting


def render_tab_allocation(project, board, rules, output_mode, extra_walls, stud_pitch_base: int):
    current_lang = st.session_state.language
    panels = st.session_state.results.get("panels", [])
    structural_system = st.session_state.get("structural_system", None)
    wall_info_base = calculate_corner_winning_rules(project.room.polygon, project.room.wall_thickness)
    wall_info_extra = extra_walls_to_wall_info(extra_walls)
    wall_info = {**wall_info_base, **wall_info_extra}
    H = project.room.height

    st.subheader(get_text("wall_elevation", current_lang))
    tab_labels = list(wall_info.keys())
    wall_tabs = st.tabs(tab_labels)
    for wt, wid in zip(wall_tabs, tab_labels):
        with wt:
            ops = [op for op in project.openings if op.wall == wid]
            wall_length = wall_info[wid]["length"]
            if structural_system and hasattr(structural_system, "studs"):
                wall_studs = [s for s in structural_system.studs if s.wall_id == wid]
                king_studs = [s for s in wall_studs if s.stud_type == "king"]
                regular_studs = [s for s in wall_studs if s.stud_type == "regular"]
                st.caption(f"{wid}: 間柱={len(regular_studs)}本, キングスタッド={len(king_studs)}本")
            elif wid in wall_info_extra:
                st.caption(f"{wid}: 新規壁（内壁・間仕切り）・片側面割付")
            fig_wall = create_wall_elevation_plotly(wid, wall_length, H, panels, ops, structural_system)
            st.plotly_chart(fig_wall, use_container_width=True, height=600)

    st.divider()
    st.info(get_text("color_info", current_lang))
    st.info(get_text("constraint_info", current_lang))
    st.caption("※ 新規壁（W5以降）は片側面の割付です。内壁で両面施工の場合は、同一壁を2回割付する運用で対応できます。")

    st.subheader(get_text("stud_setting", current_lang))
    stud_pitch_new = st.selectbox(
        get_text("stud_pitch", current_lang), [455, 303], index=0,
        format_func=lambda x: f"{x}mm", key="stud_pitch_allocation"
    )
    if st.button(get_text("recalculate", current_lang)):
        panels, errors = allocate_walls_with_architectural_constraints(
            project, board, rules, output_mode, stud_pitch_new, extra_walls=extra_walls
        )
        placements, util, num_sheets = simple_nesting(panels, board, rules, False)
        st.session_state.results = {
            "panels": panels, "errors": errors, "placements": placements,
            "utilization": util, "num_sheets": num_sheets, "alloc_time": 0
        }
        st.success(f"{get_text('stud_pitch', current_lang)} {stud_pitch_new}mm {get_text('recalculated', current_lang)}")
        st.rerun()

    if st.button(get_text("auto_fix", current_lang)):
        fixed = []
        for p in panels:
            if p.w < rules.min_piece:
                p.note = (p.note or "") + " / 最小片違反"
            fixed.append(p)
        st.session_state.results["panels"] = fixed
        st.success(get_text("auto_fixed", current_lang))
