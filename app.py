"""
割付・板取 PoC - エントリポイント
"""
import streamlit as st

from src.i18n import get_text
from src.input import load_demo_project
from src.cedxm import create_board_from_height
from src.masterdata import default_master, Project, BoardMaster, Rules
from src.allocating import allocate_walls_with_architectural_constraints, extra_walls_to_wall_info
from src.nesting import simple_nesting
from src.ui import (
    render_sidebar,
    render_tab_project,
    render_tab_allocation,
    render_tab_nesting,
    render_tab_drawings,
    render_tab_master,
    render_tab_settings,
)

# =========================
# ページ設定・セッション初期化
# =========================

st.set_page_config(page_title="Panel Allocation & Nesting PoC", layout="wide")

if "project" not in st.session_state:
    st.session_state.project = load_demo_project()
if "board" not in st.session_state:
    _b, r, mode = default_master()
    st.session_state.board = create_board_from_height(st.session_state.project.room.height)
    st.session_state.rules = r
    st.session_state.output_mode = mode
if "results" not in st.session_state:
    st.session_state.results = {}
if "language" not in st.session_state:
    st.session_state.language = "ja"

current_lang = st.session_state.language
st.title(get_text("app_title", current_lang))
st.caption(get_text("app_caption", current_lang))

# =========================
# サイドバー
# =========================

with st.sidebar:
    run = render_sidebar()

stud_pitch = 455
prefer_y_long = False

# =========================
# タブ作成
# =========================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    get_text("tab_project", current_lang),
    get_text("tab_allocation", current_lang),
    get_text("tab_nesting", current_lang),
    get_text("tab_drawings", current_lang),
    get_text("tab_master", current_lang),
    get_text("tab_settings", current_lang),
])

project: Project = st.session_state.project
board: BoardMaster = st.session_state.board
rules: Rules = st.session_state.rules
output_mode: str = st.session_state.output_mode
extra_walls = st.session_state.get("extra_walls", [])

# =========================
# 実行時：割付・板取
# =========================

if run:
    panels, errors = allocate_walls_with_architectural_constraints(
        project, board, rules, output_mode, stud_pitch, extra_walls=extra_walls
    )
    placements, util, num_sheets = simple_nesting(panels, board, rules, prefer_y_long)
    alloc_time = next((e["sec"] for e in errors if e.get("code") == "INFO-TIME" and e.get("phase") == "allocation"), 0)
    st.session_state.results = {
        "panels": panels,
        "errors": errors,
        "placements": placements,
        "utilization": util,
        "num_sheets": num_sheets,
        "alloc_time": alloc_time,
    }
    from src.structural import generate_structural_system
    st.session_state.structural_system = generate_structural_system(project, "S", stud_pitch)
    st.success(get_text("execution_success", current_lang).format(pitch=stud_pitch, board=board.name))

# =========================
# 各タブの描画
# =========================

with tab1:
    render_tab_project(project, stud_pitch, prefer_y_long)

with tab2:
    render_tab_allocation(project, board, rules, output_mode, extra_walls, stud_pitch)

with tab3:
    render_tab_nesting(board)

with tab4:
    render_tab_drawings(board)

with tab5:
    render_tab_master(board, rules, output_mode)

with tab6:
    render_tab_settings()

# =========================
# フッター
# =========================

st.caption(get_text("footer_note1", current_lang))
st.caption(get_text("footer_note2", current_lang))
