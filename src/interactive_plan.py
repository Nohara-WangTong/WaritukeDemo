"""
インタラクティブな平面図編集機能
Streamlitとplotlyを使用したマウス操作による壁作成
"""
import streamlit as st
import plotly.graph_objects as go
from typing import List, Tuple, Optional
from src.wall_editor import (
    WallSegment, snap_to_grid, snap_to_horizontal_or_vertical,
    create_wall_from_line, create_walls_from_area, find_nearest_wall_point
)
from src.masterdata import Project
from src.allocating import calculate_corner_winning_rules

def create_interactive_plan_editor(project: Project, key_prefix: str = "plan_editor"):
    """
    インタラクティブな平面図エディタ
    
    機能：
    1. マウスで線を描いて壁作成
    2. マウスでエリアを描いて部屋作成
    """
    
    # セッション状態の初期化
    if f"{key_prefix}_mode" not in st.session_state:
        st.session_state[f"{key_prefix}_mode"] = "view"  # view, draw_wall, draw_room
    if f"{key_prefix}_points" not in st.session_state:
        st.session_state[f"{key_prefix}_points"] = []
    if f"{key_prefix}_new_walls" not in st.session_state:
        st.session_state[f"{key_prefix}_new_walls"] = []
    
    # 既存の壁をWallSegment形式に変換
    wall_info = calculate_corner_winning_rules(project.room.polygon, project.room.wall_thickness)
    existing_walls = []
    for wid in ["W1", "W2", "W3", "W4"]:
        wall = wall_info[wid]
        existing_walls.append(WallSegment(
            id=wid,
            start=wall["start"],
            end=wall["end"],
            thickness=project.room.wall_thickness,
            height=project.room.height,
            is_new=False
        ))
    
    # 新規作成された壁を追加
    all_walls = existing_walls + st.session_state[f"{key_prefix}_new_walls"]
    
    # コントロールパネル
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("🖱️ 壁を描く", use_container_width=True, 
                    type="primary" if st.session_state[f"{key_prefix}_mode"] == "draw_wall" else "secondary"):
            st.session_state[f"{key_prefix}_mode"] = "draw_wall"
            st.session_state[f"{key_prefix}_points"] = []
            st.rerun()
    
    with col2:
        if st.button("🔲 部屋を描く", use_container_width=True,
                    type="primary" if st.session_state[f"{key_prefix}_mode"] == "draw_room" else "secondary"):
            st.session_state[f"{key_prefix}_mode"] = "draw_room"
            st.session_state[f"{key_prefix}_points"] = []
            st.rerun()
    
    with col3:
        if st.button("👁️ 表示モード", use_container_width=True,
                    type="primary" if st.session_state[f"{key_prefix}_mode"] == "view" else "secondary"):
            st.session_state[f"{key_prefix}_mode"] = "view"
            st.session_state[f"{key_prefix}_points"] = []
            st.rerun()
    
    with col4:
        if st.button("🗑️ クリア", use_container_width=True):
            st.session_state[f"{key_prefix}_points"] = []
            st.rerun()
    
    with col5:
        if st.button("↩️ 元に戻す", use_container_width=True):
            if st.session_state[f"{key_prefix}_new_walls"]:
                st.session_state[f"{key_prefix}_new_walls"].pop()
                st.rerun()
    
    current_mode = st.session_state[f"{key_prefix}_mode"]
    mode_text = {
        "view": "👁️ 表示モード",
        "draw_wall": "🖱️ 壁作成モード：図上をクリックで点を追加（始点・終点の順に2点）。水平・垂直方向の壁を作成します。",
        "draw_room": "🔲 部屋作成モード：図上をドラッグで四角を描くと4頂点が追加されます。その後「部屋を作成」を押してください。"
    }
    st.info(mode_text.get(current_mode, ""))
    
    fig = create_editable_plan_figure(
        project, all_walls, st.session_state[f"{key_prefix}_points"], mode=current_mode
    )
    plot_config = {"scrollZoom": False} if current_mode in ("draw_wall", "draw_room") else None
    if current_mode == "draw_wall":
        selection_mode = ("points",)
    elif current_mode == "draw_room":
        selection_mode = ("box",)
    else:
        selection_mode = ("points", "box")
    event = st.plotly_chart(
        fig,
        use_container_width=True,
        key=f"{key_prefix}_chart",
        on_select="rerun" if current_mode in ("draw_wall", "draw_room") else "ignore",
        selection_mode=selection_mode,
        config=plot_config
    )
    
    if current_mode == "draw_wall" and event and getattr(event, "selection", None):
        sel = event.selection
        pts = getattr(sel, "points", None) or []
        for p in pts:
            if getattr(p, "curve_number", None) == 0:
                x, y = getattr(p, "x", None), getattr(p, "y", None)
                if x is not None and y is not None:
                    st.session_state[f"{key_prefix}_points"].append(snap_to_grid((float(x), float(y))))
                    st.rerun()
                break
    
    if current_mode == "draw_room" and event and getattr(event, "selection", None):
        sel = event.selection
        box_list = getattr(sel, "box", None) or []
        if box_list:
            b = box_list[0] if isinstance(box_list[0], dict) else {}
            if not isinstance(b, dict):
                b = {}
            x0, x1 = b.get("x0"), b.get("x1")
            y0, y1 = b.get("y0"), b.get("y1")
            if "range" in b and len(b["range"]) >= 2:
                r = b["range"]
                x0, x1 = r[0][0], r[0][1]
                y0, y1 = r[1][0], r[1][1]
            if x0 is not None and x1 is not None and y0 is not None and y1 is not None:
                for pt in [
                    snap_to_grid((float(x0), float(y0))),
                    snap_to_grid((float(x1), float(y0))),
                    snap_to_grid((float(x1), float(y1))),
                    snap_to_grid((float(x0), float(y1))),
                ]:
                    st.session_state[f"{key_prefix}_points"].append(pt)
                st.rerun()
    
    if st.session_state[f"{key_prefix}_mode"] == "draw_wall":
        st.write("### 📍 図上をクリックで点を追加（始点・終点の順に2点）。または座標入力：")
    elif st.session_state[f"{key_prefix}_mode"] == "draw_room":
        st.write("### 📍 図上をドラッグで四角を描くと4頂点が追加されます。または座標入力で点を追加：")
    if st.session_state[f"{key_prefix}_mode"] in ["draw_wall", "draw_room"]:
        col_x, col_y, col_add = st.columns([2, 2, 1])
        
        with col_x:
            x_coord = st.number_input("X座標 (mm)", value=0, step=100, key=f"{key_prefix}_x")
        with col_y:
            y_coord = st.number_input("Y座標 (mm)", value=0, step=100, key=f"{key_prefix}_y")
        with col_add:
            st.write("")  # スペース
            st.write("")  # スペース
            if st.button("➕ 点を追加", use_container_width=True):
                # グリッドにスナップ
                snapped = snap_to_grid((x_coord, y_coord))
                st.session_state[f"{key_prefix}_points"].append(snapped)
                st.rerun()
        
        # 現在の点を表示
        if st.session_state[f"{key_prefix}_points"]:
            st.write(f"**追加された点:** {len(st.session_state[f'{key_prefix}_points'])}個")
            for i, pt in enumerate(st.session_state[f"{key_prefix}_points"]):
                st.write(f"  {i+1}. ({pt[0]}, {pt[1]})")
    
    # 壁作成ボタン（水平・垂直方向限定）
    if st.session_state[f"{key_prefix}_mode"] == "draw_wall" and len(st.session_state[f"{key_prefix}_points"]) >= 2:
        st.caption("始点・終点から水平または垂直の壁を作成します。")
        if st.button("✅ 壁を作成", type="primary", use_container_width=True):
            # 最初の2点から壁を作成
            start = st.session_state[f"{key_prefix}_points"][0]
            end = st.session_state[f"{key_prefix}_points"][1]
            
            new_wall = create_wall_from_line(
                start, end,
                project.room.wall_thickness,
                project.room.height,
                all_walls
            )
            
            if new_wall:
                st.session_state[f"{key_prefix}_new_walls"].append(new_wall)
                st.session_state[f"{key_prefix}_points"] = []
                st.success(f"✅ 壁 {new_wall.id} を作成しました！")
                st.rerun()
            else:
                st.error("❌ 壁を作成できませんでした（長さが短すぎます）")
    
    # 部屋作成ボタン
    if st.session_state[f"{key_prefix}_mode"] == "draw_room" and len(st.session_state[f"{key_prefix}_points"]) >= 2:
        if st.button("✅ 部屋を作成", type="primary", use_container_width=True):
            new_walls = create_walls_from_area(
                st.session_state[f"{key_prefix}_points"],
                project.room.wall_thickness,
                project.room.height,
                all_walls
            )
            
            if new_walls:
                st.session_state[f"{key_prefix}_new_walls"].extend(new_walls)
                st.session_state[f"{key_prefix}_points"] = []
                st.success(f"✅ {len(new_walls)}個の壁を作成しました！")
                st.rerun()
            else:
                st.error("❌ 部屋を作成できませんでした（サイズが小さすぎます）")
    
    # 新規作成された壁の情報を表示
    if st.session_state[f"{key_prefix}_new_walls"]:
        st.write("### 🆕 新規作成された壁")
        for wall in st.session_state[f"{key_prefix}_new_walls"]:
            length = ((wall.end[0] - wall.start[0])**2 + (wall.end[1] - wall.start[1])**2)**0.5
            st.write(f"- **{wall.id}**: 始点({wall.start[0]}, {wall.start[1]}) → 終点({wall.end[0]}, {wall.end[1]}) | 長さ: {length:.0f}mm")
    
    return st.session_state[f"{key_prefix}_new_walls"]

def create_editable_plan_figure(project: Project, walls: List[WallSegment], 
                                current_points: List[Tuple[int, int]],
                                mode: str = "view") -> go.Figure:
    """編集可能な平面図を作成。draw時はPan禁止・選択で座標取得。"""
    fig = go.Figure()
    wall_info = calculate_corner_winning_rules(project.room.polygon, project.room.wall_thickness)
    min_x = min(w["start"][0] for w in wall_info.values())
    max_x = max(w["end"][0] for w in wall_info.values())
    min_y = min(w["start"][1] for w in wall_info.values())
    max_y = max(w["end"][1] for w in wall_info.values())
    grid_margin = 1000
    grid_min_x = min_x - grid_margin
    grid_max_x = max_x + grid_margin
    grid_min_y = min_y - grid_margin
    grid_max_y = max_y + grid_margin
    
    grid_step = 100
    grid_x = list(range(int(grid_min_x), int(grid_max_x) + 1, grid_step))
    grid_y = list(range(int(grid_min_y), int(grid_max_y) + 1, grid_step))
    click_x, click_y = [], []
    for gx in grid_x:
        for gy in grid_y:
            click_x.append(gx)
            click_y.append(gy)
    if click_x:
        fig.add_trace(go.Scatter(
            x=click_x, y=click_y,
            mode='markers',
            marker=dict(size=5, opacity=0.2, color='gray', symbol='circle'),
            name='_click_grid_',
            legendgroup='_click_grid_',
            hovertemplate='クリックでここに点を追加<extra></extra>',
            showlegend=False
        ))
    
    grid_size = 500
    for x in range(int(grid_min_x), int(grid_max_x) + 1, grid_size):
        fig.add_trace(go.Scatter(
            x=[x, x], y=[grid_min_y, grid_max_y],
            mode='lines',
            line=dict(color='lightgray', width=0.5, dash='dot'),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    for y in range(int(grid_min_y), int(grid_max_y) + 1, grid_size):
        fig.add_trace(go.Scatter(
            x=[grid_min_x, grid_max_x], y=[y, y],
            mode='lines',
            line=dict(color='lightgray', width=0.5, dash='dot'),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # 既存の壁を描画
    for wall in walls:
        color = 'blue' if wall.is_new else 'black'
        width = 4 if wall.is_new else 3
        
        fig.add_trace(go.Scatter(
            x=[wall.start[0], wall.end[0]],
            y=[wall.start[1], wall.end[1]],
            mode='lines+markers',
            line=dict(color=color, width=width),
            marker=dict(size=8, color=color),
            name=f'壁 {wall.id}',
            hovertemplate=f'壁 {wall.id}<br>始点: ({wall.start[0]}, {wall.start[1]})<br>終点: ({wall.end[0]}, {wall.end[1]})<br>高さ: {wall.height}mm<extra></extra>',
            showlegend=False
        ))
    
    # 現在描画中の点を表示
    if current_points:
        x_coords = [p[0] for p in current_points]
        y_coords = [p[1] for p in current_points]
        
        # 点を描画
        fig.add_trace(go.Scatter(
            x=x_coords, y=y_coords,
            mode='markers',
            marker=dict(size=12, color='red', symbol='x'),
            name='描画中の点',
            hovertemplate='点 %{pointNumber}<br>X: %{x}mm<br>Y: %{y}mm<extra></extra>',
            showlegend=False
        ))
        
        # 線を描画（2点以上の場合）
        if len(current_points) >= 2:
            fig.add_trace(go.Scatter(
                x=x_coords, y=y_coords,
                mode='lines',
                line=dict(color='red', width=2, dash='dash'),
                name='描画中の線',
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # 部屋の外形を描画
    poly = project.room.polygon + [project.room.polygon[0]]
    x_coords = [p[0] for p in poly]
    y_coords = [p[1] for p in poly]
    
    fig.add_trace(go.Scatter(
        x=x_coords, y=y_coords,
        mode='lines',
        line=dict(color='gray', width=2, dash='dash'),
        name='既存の部屋',
        fill='toself',
        fillcolor='rgba(200,200,200,0.1)',
        hovertemplate='既存の部屋<extra></extra>',
        showlegend=False
    ))
    
    fig.update_layout(
        title="平面図エディタ（マウス操作で壁作成）",
        xaxis_title="X (mm)",
        yaxis_title="Y (mm)",
        showlegend=False,
        width=1000,
        height=800,
        xaxis=dict(
            scaleanchor="y",
            scaleratio=1,
            range=[grid_min_x, grid_max_x],
            fixedrange=False
        ),
        yaxis=dict(
            range=[grid_min_y, grid_max_y],
            fixedrange=False
        ),
        hovermode='closest',
        dragmode='select' if mode in ('draw_wall', 'draw_room') else 'pan'
    )
    
    return fig
