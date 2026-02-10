"""
1. 案件ビュー（案件情報・平面図・3D見付図）
"""
import pandas as pd
import streamlit as st
from src.i18n import get_text
from src.allocating import calculate_corner_winning_rules, allocate_walls_with_architectural_constraints, extra_walls_to_wall_info
from src.visualization import create_room_plan_plotly, create_3d_elevation_view
from src.interactive_plan import create_interactive_plan_editor
from src.nesting import simple_nesting


def render_tab_project(project, stud_pitch: int, prefer_y_long: bool):
    current_lang = st.session_state.language
    board = st.session_state.board
    rules = st.session_state.rules
    output_mode = st.session_state.output_mode
    extra_walls = st.session_state.get("extra_walls", [])

    subtab1, subtab2, subtab3 = st.tabs([
        get_text("subtab_project_info", current_lang),
        get_text("subtab_plan_view", current_lang),
        get_text("subtab_3d_view", current_lang)
    ])

    with subtab1:
        st.subheader(get_text("project_info", current_lang))
        c1, c2 = st.columns([1, 1])
        with c1:
            st.write(f"**{get_text('project_id', current_lang)}**: {project.project_id}")
            st.write(f"**{get_text('project_name', current_lang)}**: {project.name}")
            st.write(f"**{get_text('room', current_lang)}**: {project.room.room_id} / {get_text('use_type', current_lang)}={project.room.use_type}, {get_text('floor', current_lang)}={project.room.floor}")
            st.write(f"**{get_text('wall_height', current_lang)}**: {project.room.height} mm")
        with c2:
            st.write(f"**{get_text('opening_list', current_lang)}**")
            df_op = pd.DataFrame([{
                "opening_id": op.opening_id,
                "wall": op.wall,
                "type": op.type,
                "width": op.width,
                "height": op.height,
                "sill_height": op.sill_height,
                "offset": op.offset_from_wall_start
            } for op in project.openings])
            st.dataframe(df_op, use_container_width=True, height=180)
            st.write(f"**{get_text('wall_info', current_lang)}**")
            if st.session_state.results:
                wall_info = calculate_corner_winning_rules(project.room.polygon, project.room.wall_thickness)
                df_wall = pd.DataFrame([{
                    "wall_id": wid,
                    "length": f"{wall['length']:.0f}mm",
                    "base_length": f"{wall['base_length']:.0f}mm",
                    "direction": wall['direction']
                } for wid, wall in wall_info.items()])
                st.dataframe(df_wall, use_container_width=True, height=180)

        st.divider()
        st.subheader(get_text("kpi_summary", current_lang))
        res = st.session_state.results
        util = res.get("utilization", 0.0)
        sheets = res.get("num_sheets", 0)
        errors = res.get("errors", [])
        err_count = len([e for e in errors if str(e.get("code", "")).startswith("E-")])
        c1, c2, c3 = st.columns(3)
        c1.metric(get_text("yield_rate", current_lang), f"{util * 100:.1f}%")
        c2.metric(get_text("sheet_count", current_lang), f"{sheets}")
        c3.metric(get_text("error_count", current_lang), f"{err_count}")

    if "structural_system" not in st.session_state:
        from src.structural import generate_structural_system
        st.session_state.structural_system = generate_structural_system(project, "S", stud_pitch)
    structural_system = st.session_state.structural_system

    with subtab2:
        st.subheader(get_text("plan_preview", current_lang))
        edit_mode = st.toggle("🖊️ 壁編集モード", value=False, key="wall_edit_mode")
        if edit_mode:
            st.info("💡 壁編集モード：マウス操作で壁を作成できます")
            new_walls = create_interactive_plan_editor(project, key_prefix="plan_editor")
            if new_walls:
                if st.button(get_text("apply_new_walls", current_lang), type="primary", use_container_width=True):
                    st.session_state.extra_walls = list(new_walls)
                    panels, errors = allocate_walls_with_architectural_constraints(
                        project, board, rules, output_mode, stud_pitch,
                        extra_walls=st.session_state.extra_walls
                    )
                    placements, util, num_sheets = simple_nesting(panels, board, rules, prefer_y_long)
                    alloc_time = next((e.get("sec", 0) for e in errors if e.get("code") == "INFO-TIME" and e.get("phase") == "allocation"), 0)
                    st.session_state.results = {
                        "panels": panels, "errors": errors, "placements": placements,
                        "utilization": util, "num_sheets": num_sheets, "alloc_time": alloc_time
                    }
                    st.success("✅ 新規壁を割付・板取に反映しました。「2. 割付ビュー」「3. 板取ビュー」で確認できます。")
                    st.rerun()
        else:
            fig_plan = create_room_plan_plotly(project, structural_system)
            st.plotly_chart(fig_plan, use_container_width=True, height=800)

    with subtab3:
        st.subheader(get_text("3d_elevation", current_lang))
        panels = st.session_state.results.get("panels", [])
        if panels or structural_system:
            wall_info_3d = {
                **calculate_corner_winning_rules(project.room.polygon, project.room.wall_thickness),
                **extra_walls_to_wall_info(st.session_state.get("extra_walls", []))
            }
            fig_3d = create_3d_elevation_view(project, panels, structural_system, wall_info=wall_info_3d)
            st.plotly_chart(fig_3d, use_container_width=True, height=800)
        else:
            st.info(get_text("3d_info", current_lang))
