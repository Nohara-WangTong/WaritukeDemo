"""
Plotlyを使用した可視化機能
"""
import math
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List
from src.masterdata import Project, Panel, BoardMaster, NestPlacement, Opening
from src.logic import place_opening_position
from src.allocating import calculate_corner_winning_rules

# 統一カラーパレット
PANEL_COLORS = {
    "good": "lightgreen",      # 真物：薄緑
    "semi": "lightblue",       # セミ：薄青
    "full": "lightblue",       # フル：薄青
    "cut": "lightblue",        # 端材：薄青
    "opening": "darkred"       # 開口部：暗い赤
}

def get_panel_color(panel: Panel) -> str:
    """パネルの種類に応じた色を返す"""
    if panel.is_cut_piece:
        return PANEL_COLORS["cut"]
    # 出力モードに基づく色分け（将来的な拡張用）
    # 現在は真物として薄緑を使用
    return PANEL_COLORS["good"]

def create_room_plan_plotly(project: Project):
    """Plotlyを使用した平面プレビュー（CAD図面描画エンジン）- パネル割付結果も表示"""
    fig = go.Figure()
    
    # 出隅ルールを適用した壁情報を取得
    wall_info = calculate_corner_winning_rules(project.room.polygon, project.room.wall_thickness)
    
    # 部屋外形の描画（外側の線）
    poly = project.room.polygon + [project.room.polygon[0]]  # 閉じた多角形
    x_coords = [p[0] for p in poly]
    y_coords = [p[1] for p in poly]
    
    fig.add_trace(go.Scatter(
        x=x_coords, y=y_coords,
        mode='lines',
        line=dict(color='black', width=3),
        name='部屋外形',
        hovertemplate='部屋外形<br>X: %{x}mm<br>Y: %{y}mm<extra></extra>'
    ))
    
    # 壁厚さを考慮した内側の線
    inner_poly = []
    for wid in ["W1", "W2", "W3", "W4"]:
        # 内側の線は壁厚分内側に配置
        wall = wall_info[wid]
        if wall["direction"] == "horizontal":
            if wid == "W1":  # 下壁
                inner_start = (wall["start"][0], wall["start"][1] + project.room.wall_thickness)
                inner_end = (wall["end"][0], wall["end"][1] + project.room.wall_thickness)
            else:  # W3 上壁
                inner_start = (wall["start"][0], wall["start"][1] - project.room.wall_thickness)
                inner_end = (wall["end"][0], wall["end"][1] - project.room.wall_thickness)
        else:  # vertical
            if wid == "W2":  # 右壁
                inner_start = (wall["start"][0] - project.room.wall_thickness, wall["start"][1])
                inner_end = (wall["end"][0] - project.room.wall_thickness, wall["end"][1])
            else:  # W4 左壁
                inner_start = (wall["start"][0] + project.room.wall_thickness, wall["start"][1])
                inner_end = (wall["end"][0] + project.room.wall_thickness, wall["end"][1])
        
        inner_poly.append(inner_start)
    
    inner_poly.append(inner_poly[0])  # 閉じる
    
    inner_x = [p[0] for p in inner_poly]
    inner_y = [p[1] for p in inner_poly]
    
    fig.add_trace(go.Scatter(
        x=inner_x, y=inner_y,
        mode='lines',
        line=dict(color='gray', width=2, dash='dash'),
        name='内側線（壁厚考慮）',
        hovertemplate='内側線<br>X: %{x}mm<br>Y: %{y}mm<extra></extra>'
    ))
    
    # 壁面の塗りつぶし（壁厚さ表示）
    wall_colors = {'W1': 'rgba(173,216,230,0.3)', 'W2': 'rgba(144,238,144,0.3)', 
                   'W3': 'rgba(240,128,128,0.3)', 'W4': 'rgba(255,255,224,0.3)'}
    
    for wid in ["W1", "W2", "W3", "W4"]:
        wall = wall_info[wid]
        
        # 壁の4つの角を定義（外側と内側）
        if wall["direction"] == "horizontal":
            if wid == "W1":  # 下壁
                wall_x = [wall["start"][0], wall["end"][0], 
                         wall["end"][0], wall["start"][0], wall["start"][0]]
                wall_y = [wall["start"][1], wall["end"][1], 
                         wall["end"][1] + project.room.wall_thickness, 
                         wall["start"][1] + project.room.wall_thickness, wall["start"][1]]
            else:  # W3 上壁
                wall_x = [wall["start"][0], wall["end"][0], 
                         wall["end"][0], wall["start"][0], wall["start"][0]]
                wall_y = [wall["start"][1], wall["end"][1], 
                         wall["end"][1] - project.room.wall_thickness, 
                         wall["start"][1] - project.room.wall_thickness, wall["start"][1]]
        else:  # vertical
            if wid == "W2":  # 右壁
                wall_x = [wall["start"][0], wall["end"][0], 
                         wall["end"][0] - project.room.wall_thickness, 
                         wall["start"][0] - project.room.wall_thickness, wall["start"][0]]
                wall_y = [wall["start"][1], wall["end"][1], 
                         wall["end"][1], wall["start"][1], wall["start"][1]]
            else:  # W4 左壁
                wall_x = [wall["start"][0], wall["end"][0], 
                         wall["end"][0] + project.room.wall_thickness, 
                         wall["start"][0] + project.room.wall_thickness, wall["start"][0]]
                wall_y = [wall["start"][1], wall["end"][1], 
                         wall["end"][1], wall["start"][1], wall["start"][1]]
        
        fig.add_trace(go.Scatter(
            x=wall_x, y=wall_y,
            fill='toself',
            fillcolor=wall_colors.get(wid, 'rgba(200,200,200,0.3)'),
            line=dict(color='gray', width=1),
            mode='lines',
            name=f'壁 {wid}',
            hovertemplate=f'壁 {wid}<br>長さ: {wall["length"]:.0f}mm<br>厚さ: {project.room.wall_thickness:.0f}mm<extra></extra>'
        ))
    
    # 壁ラベルの追加
    for wid in ["W1", "W2", "W3", "W4"]:
        wall = wall_info[wid]
        center_x = (wall["start"][0] + wall["end"][0]) / 2
        center_y = (wall["start"][1] + wall["end"][1]) / 2
        
        fig.add_annotation(
            x=center_x, y=center_y,
            text=f'{wid}<br>{wall["length"]:.0f}mm',
            showarrow=False,
            font=dict(size=12, color='blue'),
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='blue',
            borderwidth=1
        )
    
    # パネル割付結果の表示（平面図上）- 壁の内側面に配置
    panels = st.session_state.results.get("panels", [])
    if panels:
        # ボード厚さを取得（デフォルト12.5mm）
        board_thickness = getattr(st.session_state.get("board", None), "thickness", 12.5)
        
        for panel in panels:
            wall = wall_info[panel.wall_id]
            
            # パネルの位置を壁の内側面に計算
            if wall["direction"] == "horizontal":
                # 横壁の場合
                panel_start_x = wall["start"][0] + (panel.x0 / wall["length"]) * (wall["end"][0] - wall["start"][0])
                panel_end_x = wall["start"][0] + ((panel.x0 + panel.w) / wall["length"]) * (wall["end"][0] - wall["start"][0])
                
                # 壁の内側面に配置
                if panel.wall_id == "W1":  # 下壁 - 内側は上側
                    panel_y = wall["start"][1] + project.room.wall_thickness - board_thickness/2
                else:  # W3 上壁 - 内側は下側
                    panel_y = wall["start"][1] - project.room.wall_thickness + board_thickness/2
                
                fig.add_trace(go.Scatter(
                    x=[panel_start_x, panel_end_x],
                    y=[panel_y, panel_y],
                    mode='lines',
                    line=dict(color=get_panel_color(panel), width=8),
                    name=f'パネル {panel.wall_id}',
                    hovertemplate=f'パネル {panel.wall_id}<br>幅: {panel.w:.0f}mm<br>厚さ: {board_thickness:.1f}mm<br>ボード: B{panel.board_number}-P{panel.part_number}<br>端材: {"Yes" if panel.is_cut_piece else "No"}<br>備考: {panel.note}<extra></extra>',
                    showlegend=False
                ))
            else:
                # 縦壁の場合
                panel_start_y = wall["start"][1] + (panel.x0 / wall["length"]) * (wall["end"][1] - wall["start"][1])
                panel_end_y = wall["start"][1] + ((panel.x0 + panel.w) / wall["length"]) * (wall["end"][1] - wall["start"][1])
                
                # 壁の内側面に配置
                if panel.wall_id == "W2":  # 右壁 - 内側は左側
                    panel_x = wall["start"][0] - project.room.wall_thickness + board_thickness/2
                else:  # W4 左壁 - 内側は右側
                    panel_x = wall["start"][0] + project.room.wall_thickness - board_thickness/2
                
                fig.add_trace(go.Scatter(
                    x=[panel_x, panel_x],
                    y=[panel_start_y, panel_end_y],
                    mode='lines',
                    line=dict(color=get_panel_color(panel), width=8),
                    name=f'パネル {panel.wall_id}',
                    hovertemplate=f'パネル {panel.wall_id}<br>幅: {panel.w:.0f}mm<br>厚さ: {board_thickness:.1f}mm<br>ボード: B{panel.board_number}-P{panel.part_number}<br>端材: {"Yes" if panel.is_cut_piece else "No"}<br>備考: {panel.note}<extra></extra>',
                    showlegend=False
                ))
    
    # 開口の可視化
    for op in project.openings:
        wall = wall_info[op.wall]
        L = wall["length"]
        off = place_opening_position(L, op)
        
        if wall["direction"] == "horizontal":
            ox = wall["start"][0] + (off / L) * (wall["end"][0] - wall["start"][0])
            ex = wall["start"][0] + ((off + op.width) / L) * (wall["end"][0] - wall["start"][0])
            oy = ey = wall["start"][1]
        else:
            oy = wall["start"][1] + (off / L) * (wall["end"][1] - wall["start"][1])
            ey = wall["start"][1] + ((off + op.width) / L) * (wall["end"][1] - wall["start"][1])
            ox = ex = wall["start"][0]
        
        fig.add_trace(go.Scatter(
            x=[ox, ex], y=[oy, ey],
            mode='lines',
            line=dict(color=PANEL_COLORS["opening"], width=8),
            name=f"開口部: {op.opening_id}",
            hovertemplate=f'開口部: {op.opening_id}<br>種類: {op.type}<br>幅: {op.width}mm<br>高さ: {op.height}mm<extra></extra>'
        ))
    
    # 部屋情報の表示
    room_center_x = sum(p[0] for p in project.room.polygon) / 4
    room_center_y = sum(p[1] for p in project.room.polygon) / 4
    
    fig.add_annotation(
        x=room_center_x, y=room_center_y,
        text=f"{project.name}<br>{project.room.room_id}<br>高さ: {project.room.height}mm<br>壁厚: {project.room.wall_thickness}mm",
        showarrow=False,
        font=dict(size=12, color='gray'),
        bgcolor='rgba(255,255,255,0.9)',
        bordercolor='gray',
        borderwidth=1
    )
    
    fig.update_layout(
        title="平面プレビュー（建築的制約対応）- ボード配置：壁内側面、間柱グリッド・出隅ルール・開口クリッピング",
        xaxis_title="X (mm)",
        yaxis_title="Y (mm)",
        showlegend=True,
        width=900,
        height=700,
        xaxis=dict(scaleanchor="y", scaleratio=1),
        hovermode='closest'
    )
    
    return fig

def create_3d_elevation_view(project: Project, panels: List[Panel]):
    """3D表示見付図（立体的な壁面表示）- 建築的制約に基づく正確な表示"""
    fig = go.Figure()
    
    # 出隅ルールを適用した壁情報を取得
    wall_info = calculate_corner_winning_rules(project.room.polygon, project.room.wall_thickness)
    height = project.room.height
    
    # 床面（外側）
    floor_x = [p[0] for p in project.room.polygon] + [project.room.polygon[0][0]]
    floor_y = [p[1] for p in project.room.polygon] + [project.room.polygon[0][1]]
    floor_z = [0] * len(floor_x)
    
    fig.add_trace(go.Scatter3d(
        x=floor_x, y=floor_y, z=floor_z,
        mode='lines',
        line=dict(color='black', width=4),
        name='床面（外側）',
        hovertemplate='床面<br>X: %{x}mm<br>Y: %{y}mm<extra></extra>'
    ))
    
    # 床面（内側）
    inner_floor_x = []
    inner_floor_y = []
    for wid in ["W1", "W2", "W3", "W4"]:
        wall = wall_info[wid]
        if wall["direction"] == "horizontal":
            if wid == "W1":  # 下壁
                inner_floor_x.append(wall["start"][0])
                inner_floor_y.append(wall["start"][1] + project.room.wall_thickness)
            else:  # W3 上壁
                inner_floor_x.append(wall["start"][0])
                inner_floor_y.append(wall["start"][1] - project.room.wall_thickness)
        else:  # vertical
            if wid == "W2":  # 右壁
                inner_floor_x.append(wall["start"][0] - project.room.wall_thickness)
                inner_floor_y.append(wall["start"][1])
            else:  # W4 左壁
                inner_floor_x.append(wall["start"][0] + project.room.wall_thickness)
                inner_floor_y.append(wall["start"][1])
    
    inner_floor_x.append(inner_floor_x[0])
    inner_floor_y.append(inner_floor_y[0])
    inner_floor_z = [0] * len(inner_floor_x)
    
    fig.add_trace(go.Scatter3d(
        x=inner_floor_x, y=inner_floor_y, z=inner_floor_z,
        mode='lines',
        line=dict(color='gray', width=2, dash='dash'),
        name='床面（内側）',
        hovertemplate='床面（内側）<br>X: %{x}mm<br>Y: %{y}mm<extra></extra>'
    ))
    
    # 天井面（外側と内側）
    ceiling_z = [height] * len(floor_x)
    inner_ceiling_z = [height] * len(inner_floor_x)
    
    fig.add_trace(go.Scatter3d(
        x=floor_x, y=floor_y, z=ceiling_z,
        mode='lines',
        line=dict(color='black', width=4),
        name='天井面（外側）',
        hovertemplate='天井面<br>X: %{x}mm<br>Y: %{y}mm<br>Z: %{z}mm<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter3d(
        x=inner_floor_x, y=inner_floor_y, z=inner_ceiling_z,
        mode='lines',
        line=dict(color='gray', width=2, dash='dash'),
        name='天井面（内側）',
        hovertemplate='天井面（内側）<br>X: %{x}mm<br>Y: %{y}mm<br>Z: %{z}mm<extra></extra>'
    ))
    
    # 壁面の3D表示（厚さを持った壁）
    wall_colors = {'W1': 'lightblue', 'W2': 'lightgreen', 'W3': 'lightcoral', 'W4': 'lightyellow'}
    
    for wid in ["W1", "W2", "W3", "W4"]:
        wall = wall_info[wid]
        
        # 壁の外側面と内側面を定義
        if wall["direction"] == "horizontal":
            if wid == "W1":  # 下壁
                outer_x = [wall["start"][0], wall["end"][0], wall["end"][0], wall["start"][0]]
                outer_y = [wall["start"][1], wall["end"][1], wall["end"][1], wall["start"][1]]
                inner_x = [wall["start"][0], wall["end"][0], wall["end"][0], wall["start"][0]]
                inner_y = [wall["start"][1] + project.room.wall_thickness, 
                          wall["end"][1] + project.room.wall_thickness,
                          wall["end"][1] + project.room.wall_thickness, 
                          wall["start"][1] + project.room.wall_thickness]
            else:  # W3 上壁
                outer_x = [wall["start"][0], wall["end"][0], wall["end"][0], wall["start"][0]]
                outer_y = [wall["start"][1], wall["end"][1], wall["end"][1], wall["start"][1]]
                inner_x = [wall["start"][0], wall["end"][0], wall["end"][0], wall["start"][0]]
                inner_y = [wall["start"][1] - project.room.wall_thickness, 
                          wall["end"][1] - project.room.wall_thickness,
                          wall["end"][1] - project.room.wall_thickness, 
                          wall["start"][1] - project.room.wall_thickness]
        else:  # vertical
            if wid == "W2":  # 右壁
                outer_x = [wall["start"][0], wall["end"][0], wall["end"][0], wall["start"][0]]
                outer_y = [wall["start"][1], wall["end"][1], wall["end"][1], wall["start"][1]]
                inner_x = [wall["start"][0] - project.room.wall_thickness, 
                          wall["end"][0] - project.room.wall_thickness,
                          wall["end"][0] - project.room.wall_thickness, 
                          wall["start"][0] - project.room.wall_thickness]
                inner_y = [wall["start"][1], wall["end"][1], wall["end"][1], wall["start"][1]]
            else:  # W4 左壁
                outer_x = [wall["start"][0], wall["end"][0], wall["end"][0], wall["start"][0]]
                outer_y = [wall["start"][1], wall["end"][1], wall["end"][1], wall["start"][1]]
                inner_x = [wall["start"][0] + project.room.wall_thickness, 
                          wall["end"][0] + project.room.wall_thickness,
                          wall["end"][0] + project.room.wall_thickness, 
                          wall["start"][0] + project.room.wall_thickness]
                inner_y = [wall["start"][1], wall["end"][1], wall["end"][1], wall["start"][1]]
        
        outer_z = [0, 0, height, height]
        inner_z = [0, 0, height, height]
        
        # 外側面のメッシュ
        fig.add_trace(go.Mesh3d(
            x=outer_x,
            y=outer_y,
            z=outer_z,
            i=[0, 0],
            j=[1, 2],
            k=[2, 3],
            color=wall_colors.get(wid, 'lightgray'),
            opacity=0.4,
            name=f'壁面 {wid} (外側)',
            showlegend=False
        ))
        
        # 内側面のメッシュ
        fig.add_trace(go.Mesh3d(
            x=inner_x,
            y=inner_y,
            z=inner_z,
            i=[0, 0],
            j=[1, 2],
            k=[2, 3],
            color=wall_colors.get(wid, 'lightgray'),
            opacity=0.2,
            name=f'壁面 {wid} (内側)',
            showlegend=False
        ))
        
        # 壁の枠線
        fig.add_trace(go.Scatter3d(
            x=outer_x + [outer_x[0]],
            y=outer_y + [outer_y[0]],
            z=outer_z + [outer_z[0]],
            mode='lines',
            line=dict(color='black', width=2),
            name=f'壁面 {wid}',
            hovertemplate=f'壁面 {wid}<br>長さ: {wall["length"]:.0f}mm<br>厚さ: {project.room.wall_thickness:.0f}mm<extra></extra>'
        ))
    
    # パネルの3D表示（内側面に配置、ボード厚さ考慮）
    board_thickness = 12.5  # デフォルトボード厚さ
    
    for panel in panels:
        wall = wall_info[panel.wall_id]
        
        # パネルの位置を内側壁面上に計算
        panel_start_ratio = panel.x0 / wall["length"]
        panel_end_ratio = (panel.x0 + panel.w) / wall["length"]
        
        if wall["direction"] == "horizontal":
            if panel.wall_id == "W1":  # 下壁 - 内側面（上側）にボードを配置
                panel_start_x = wall["start"][0] + panel_start_ratio * (wall["end"][0] - wall["start"][0])
                panel_end_x = wall["start"][0] + panel_end_ratio * (wall["end"][0] - wall["start"][0])
                # 内側面からボード厚さ分内側に配置
                panel_y = wall["start"][1] + project.room.wall_thickness - board_thickness
                panel_x = [panel_start_x, panel_end_x, panel_end_x, panel_start_x, panel_start_x]
                panel_y_coords = [panel_y, panel_y, panel_y, panel_y, panel_y]
            else:  # W3 上壁 - 内側面（下側）にボードを配置
                panel_start_x = wall["start"][0] + panel_start_ratio * (wall["end"][0] - wall["start"][0])
                panel_end_x = wall["start"][0] + panel_end_ratio * (wall["end"][0] - wall["start"][0])
                # 内側面からボード厚さ分内側に配置
                panel_y = wall["start"][1] - project.room.wall_thickness + board_thickness
                panel_x = [panel_start_x, panel_end_x, panel_end_x, panel_start_x, panel_start_x]
                panel_y_coords = [panel_y, panel_y, panel_y, panel_y, panel_y]
        else:  # vertical
            if panel.wall_id == "W2":  # 右壁 - 内側面（左側）にボードを配置
                panel_start_y = wall["start"][1] + panel_start_ratio * (wall["end"][1] - wall["start"][1])
                panel_end_y = wall["start"][1] + panel_end_ratio * (wall["end"][1] - wall["start"][1])
                # 内側面からボード厚さ分内側に配置
                panel_x_coord = wall["start"][0] - project.room.wall_thickness + board_thickness
                panel_x = [panel_x_coord, panel_x_coord, panel_x_coord, panel_x_coord, panel_x_coord]
                panel_y_coords = [panel_start_y, panel_end_y, panel_end_y, panel_start_y, panel_start_y]
            else:  # W4 左壁 - 内側面（右側）にボードを配置
                panel_start_y = wall["start"][1] + panel_start_ratio * (wall["end"][1] - wall["start"][1])
                panel_end_y = wall["start"][1] + panel_end_ratio * (wall["end"][1] - wall["start"][1])
                # 内側面からボード厚さ分内側に配置
                panel_x_coord = wall["start"][0] + project.room.wall_thickness - board_thickness
                panel_x = [panel_x_coord, panel_x_coord, panel_x_coord, panel_x_coord, panel_x_coord]
                panel_y_coords = [panel_start_y, panel_end_y, panel_end_y, panel_start_y, panel_start_y]
        
        panel_z = [panel.y0, panel.y0, panel.y0 + panel.h, panel.y0 + panel.h, panel.y0]
        
        color = get_panel_color(panel)
        
        fig.add_trace(go.Scatter3d(
            x=panel_x, y=panel_y_coords, z=panel_z,
            mode='lines',
            line=dict(color=color, width=4),
            name=f'パネル {panel.wall_id}',
            hovertemplate=f'パネル {panel.wall_id}<br>幅: {panel.w:.0f}mm<br>高さ: {panel.h:.0f}mm<br>厚さ: {board_thickness:.1f}mm<br>ボード: B{panel.board_number}-P{panel.part_number}<br>端材: {"Yes" if panel.is_cut_piece else "No"}<br>備考: {panel.note}<extra></extra>',
            showlegend=False
        ))
    
    # 開口の3D表示
    for op in project.openings:
        wall = wall_info[op.wall]
        L = wall["length"]
        off = place_opening_position(L, op)
        
        # 開口の位置計算
        opening_start_ratio = off / L
        opening_end_ratio = (off + op.width) / L
        
        if wall["direction"] == "horizontal":
            if op.wall == "W1":  # 下壁 - 内側面に配置
                op_start_x = wall["start"][0] + opening_start_ratio * (wall["end"][0] - wall["start"][0])
                op_end_x = wall["start"][0] + opening_end_ratio * (wall["end"][0] - wall["start"][0])
                # 内側面に配置
                op_y = wall["start"][1] + project.room.wall_thickness - board_thickness
                opening_x = [op_start_x, op_end_x, op_end_x, op_start_x, op_start_x]
                opening_y = [op_y, op_y, op_y, op_y, op_y]
            else:  # W3 上壁 - 内側面に配置
                op_start_x = wall["start"][0] + opening_start_ratio * (wall["end"][0] - wall["start"][0])
                op_end_x = wall["start"][0] + opening_end_ratio * (wall["end"][0] - wall["start"][0])
                # 内側面に配置
                op_y = wall["start"][1] - project.room.wall_thickness + board_thickness
                opening_x = [op_start_x, op_end_x, op_end_x, op_start_x, op_start_x]
                opening_y = [op_y, op_y, op_y, op_y, op_y]
        else:  # vertical
            if op.wall == "W2":  # 右壁 - 内側面に配置
                op_start_y = wall["start"][1] + opening_start_ratio * (wall["end"][1] - wall["start"][1])
                op_end_y = wall["start"][1] + opening_end_ratio * (wall["end"][1] - wall["start"][1])
                # 内側面に配置
                op_x = wall["start"][0] - project.room.wall_thickness + board_thickness
                opening_x = [op_x, op_x, op_x, op_x, op_x]
                opening_y = [op_start_y, op_end_y, op_end_y, op_start_y, op_start_y]
            else:  # W4 左壁 - 内側面に配置
                op_start_y = wall["start"][1] + opening_start_ratio * (wall["end"][1] - wall["start"][1])
                op_end_y = wall["start"][1] + opening_end_ratio * (wall["end"][1] - wall["start"][1])
                # 内側面に配置
                op_x = wall["start"][0] + project.room.wall_thickness - board_thickness
                opening_x = [op_x, op_x, op_x, op_x, op_x]
                opening_y = [op_start_y, op_end_y, op_end_y, op_start_y, op_start_y]
        
        # 開口の高さ
        if op.type == "door":
            op_z_start, op_z_end = 0, op.height
        else:
            op_z_start, op_z_end = op.sill_height, op.sill_height + op.height
        
        opening_z = [op_z_start, op_z_start, op_z_end, op_z_end, op_z_start]
        
        fig.add_trace(go.Scatter3d(
            x=opening_x, y=opening_y, z=opening_z,
            mode='lines',
            line=dict(color=PANEL_COLORS["opening"], width=6),
            name=f'開口部: {op.opening_id}',
            hovertemplate=f'開口部: {op.opening_id}<br>種類: {op.type}<br>幅: {op.width}mm<br>高さ: {op.height}mm<extra></extra>'
        ))
    
    fig.update_layout(
        title="3D表示見付図（建築的制約対応）",
        scene=dict(
            xaxis_title="X (mm)",
            yaxis_title="Y (mm)",
            zaxis_title="Z (mm)",
            aspectmode='data',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2)
            )
        ),
        width=1000,
        height=800,
        showlegend=True
    )
    
    return fig

def create_wall_elevation_plotly(wall_id: str, wall_len: float, H: float, panels: List[Panel], openings: List[Opening]):
    """Plotlyを使用した壁立面図 - 出隅ルール適用後の実際の壁長さを使用"""
    fig = go.Figure()
    
    # 壁の外形
    fig.add_shape(
        type="rect",
        x0=0, y0=0, x1=wall_len, y1=H,
        line=dict(color="black", width=2),
        fillcolor="rgba(240,240,240,0.3)"
    )
    
    # 開口の表示
    for op in openings:
        off = place_opening_position(wall_len, op)
        if op.type == "door":
            oy0, oy1 = 0.0, op.height
        else:
            oy0, oy1 = op.sill_height, op.sill_height + op.height
        
        fig.add_shape(
            type="rect",
            x0=off, y0=oy0, x1=off + op.width, y1=oy1,
            fillcolor=PANEL_COLORS["opening"],
            opacity=0.5,
            line=dict(color=PANEL_COLORS["opening"], width=2)
        )
        
        fig.add_annotation(
            x=off + op.width/2,
            y=oy0 + (oy1-oy0)/2,
            text=f"開口部<br>{op.opening_id}",
            showarrow=False,
            font=dict(size=10, color='white'),
            bgcolor=PANEL_COLORS["opening"]
        )
    
    # パネルの表示
    for p in panels:
        if p.wall_id != wall_id:
            continue
        
        color = get_panel_color(p)
        
        fig.add_shape(
            type="rect",
            x0=p.x0, y0=p.y0, x1=p.x0 + p.w, y1=p.y0 + p.h,
            fillcolor=color,
            opacity=0.7,
            line=dict(color="black", width=1)
        )
        
        # パネル情報の表示（ボード番号とパーツ番号を含む）
        panel_text = f"W:{p.w:.0f}mm"
        
        # ボード番号とパーツ番号を表示（板取結果がある場合）
        if p.board_number > 0 and p.part_number > 0:
            panel_text += f"<br>B{p.board_number}-P{p.part_number}"
        
        # noteフィールドに既に端材/切欠情報が含まれている場合は重複を避ける
        if p.note:
            panel_text += f"<br>{p.note}"
        else:
            # noteが空の場合のみ、is_cut_pieceとrequires_cutoutから情報を追加
            if p.is_cut_piece:
                panel_text += "<br>端材"
            if p.requires_cutout:
                panel_text += "<br>切欠要"
            
        fig.add_annotation(
            x=p.x0 + p.w/2,
            y=p.y0 + p.h/2,
            text=panel_text,
            showarrow=False,
            font=dict(size=8),
            bgcolor='white',
            bordercolor='black',
            borderwidth=1
        )
    
    fig.update_layout(
        title=f"{wall_id} 立面図（割付）- 実長: {wall_len:.0f}mm",
        xaxis_title="壁方向 (mm)",
        yaxis_title="高さ (mm)",
        width=800,
        height=400,
        xaxis=dict(range=[-50, wall_len+50]),
        yaxis=dict(range=[0, H+50]),
        showlegend=False
    )
    
    return fig

def create_nesting_plotly(placements: List[NestPlacement], board: BoardMaster):
    """Plotlyを使用した板取図"""
    if not placements:
        return None
    
    num_sheets = max(pl.sheet_id for pl in placements)
    
    # サブプロットの作成
    cols = min(3, num_sheets)
    rows = math.ceil(num_sheets / cols)
    
    fig = make_subplots(
        rows=rows, cols=cols,
        subplot_titles=[f"ボード #{i+1}" for i in range(num_sheets)],
        specs=[[{"type": "xy"}] * cols for _ in range(rows)]
    )
    
    for sid in range(1, num_sheets + 1):
        row = ((sid - 1) // cols) + 1
        col = ((sid - 1) % cols) + 1
        
        # 板の外形
        fig.add_shape(
            type="rect",
            x0=0, y0=0, x1=board.raw_width, y1=board.raw_height,
            line=dict(color="black", width=2),
            fillcolor="rgba(240,240,240,0.2)",
            row=row, col=col
        )
        
        # 配置されたパネル
        sheet_placements = [p for p in placements if p.sheet_id == sid]
        for i, pl in enumerate(sheet_placements):
            # 板取図では真物として薄緑を使用
            fig.add_shape(
                type="rect",
                x0=pl.x, y0=pl.y, x1=pl.x + pl.w, y1=pl.y + pl.h,
                fillcolor=PANEL_COLORS["good"],
                opacity=0.7,
                line=dict(color="black", width=1),
                row=row, col=col
            )
            
            # ボード番号とパーツ番号の表示
            fig.add_annotation(
                x=pl.x + pl.w/2,
                y=pl.y + pl.h/2,
                text=f"B{sid}-P{i+1}<br>{pl.w:.0f}×{pl.h:.0f}",
                showarrow=False,
                font=dict(size=8),
                bgcolor='white',
                bordercolor='black',
                borderwidth=1,
                row=row, col=col
            )
    
    fig.update_layout(
        title="板取結果",
        width=1000,
        height=600 * rows,
        showlegend=False
    )
    
    # 各サブプロットの軸設定
    for i in range(1, num_sheets + 1):
        fig.update_xaxes(
            title_text="X (mm)",
            range=[0, board.raw_width * 1.1],
            row=((i-1) // cols) + 1,
            col=((i-1) % cols) + 1
        )
        fig.update_yaxes(
            title_text="Y (mm)",
            range=[0, board.raw_height * 1.1],
            scaleanchor=f"x{i}",
            scaleratio=1,
            row=((i-1) // cols) + 1,
            col=((i-1) % cols) + 1
        )
    
    return fig