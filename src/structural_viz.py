"""
構造要素の可視化（2D平面・3D立体）
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List
import math
from src.structural import StructuralSystem, Column, Beam, Stud, GridLine

# レイヤ別カラーパレット
LAYER_COLORS = {
    "S_COL": "darkgray",      # 柱
    "S_BEAM": "black",         # 梁
    "N_STUD": "lightgray",     # 間柱
    "AXIS": "blue",            # 通り芯
    "OPEN": "orange",          # 開口
    "LINTEL": "brown",         # まぐさ
    "WARNING": "orange",       # 警告
    "VIOLATION": "red",        # 違反
    "LOCKED": "cyan",          # ロック要素
}

def create_structural_plan_view(structural_system: StructuralSystem, project, show_layers: dict = None):
    """
    2D平面プレビュー（構造要素表示）
    """
    if show_layers is None:
        show_layers = {
            "columns": True,
            "beams": True,
            "studs": True,
            "grid_lines": True,
            "openings": True
        }
    
    fig = go.Figure()
    
    # 1. 通り芯の表示
    if show_layers.get("grid_lines", True):
        for grid in structural_system.grid_lines:
            line_style = "dash" if grid.is_virtual else "solid"
            fig.add_trace(go.Scatter(
                x=[grid.start_point[0], grid.end_point[0]],
                y=[grid.start_point[1], grid.end_point[1]],
                mode='lines',
                line=dict(color=LAYER_COLORS["AXIS"], width=1, dash=line_style),
                name=f'通り芯 {grid.id}',
                hovertemplate=f'通り芯: {grid.id}<br>{"仮想" if grid.is_virtual else "実"}<extra></extra>',
                showlegend=False
            ))
            
            # 通り芯ラベル
            mid_x = (grid.start_point[0] + grid.end_point[0]) / 2
            mid_y = (grid.start_point[1] + grid.end_point[1]) / 2
            fig.add_annotation(
                x=mid_x, y=mid_y,
                text=grid.id,
                showarrow=False,
                font=dict(size=10, color=LAYER_COLORS["AXIS"]),
                bgcolor='rgba(255,255,255,0.8)'
            )
    
    # 2. 柱の表示
    if show_layers.get("columns", True):
        for col in structural_system.columns:
            color = LAYER_COLORS["LOCKED"] if col.locked else LAYER_COLORS["S_COL"]
            
            if col.section_type == "rect":
                # 矩形柱
                x0 = col.x - col.width / 2
                y0 = col.y - col.depth / 2
                x1 = col.x + col.width / 2
                y1 = col.y + col.depth / 2
                
                fig.add_shape(
                    type="rect",
                    x0=x0, y0=y0, x1=x1, y1=y1,
                    fillcolor=color,
                    opacity=0.6,
                    line=dict(color=color, width=2)
                )
            else:
                # 円形柱
                fig.add_shape(
                    type="circle",
                    x0=col.x - col.width/2, y0=col.y - col.width/2,
                    x1=col.x + col.width/2, y1=col.y + col.width/2,
                    fillcolor=color,
                    opacity=0.6,
                    line=dict(color=color, width=2)
                )
            
            # 柱ラベル
            fig.add_annotation(
                x=col.x, y=col.y,
                text=f"{col.id}<br>{col.width:.0f}×{col.depth:.0f}",
                showarrow=False,
                font=dict(size=8, color='white'),
                bgcolor=color
            )
    
    # 3. 梁の表示
    if show_layers.get("beams", True):
        for beam in structural_system.beams:
            color = LAYER_COLORS["LINTEL"] if beam.is_lintel else LAYER_COLORS["S_BEAM"]
            if beam.locked:
                color = LAYER_COLORS["LOCKED"]
            
            width = 3 if beam.is_lintel else 2
            
            fig.add_trace(go.Scatter(
                x=[beam.start_point[0], beam.end_point[0]],
                y=[beam.start_point[1], beam.end_point[1]],
                mode='lines',
                line=dict(color=color, width=width),
                name=f'{"まぐさ" if beam.is_lintel else "梁"} {beam.id}',
                hovertemplate=f'{"まぐさ" if beam.is_lintel else "梁"}: {beam.id}<br>幅: {beam.width:.0f}mm<br>梁成: {beam.depth:.0f}mm<br>{beam.note}<extra></extra>',
                showlegend=False
            ))
            
            # 梁ラベル
            mid_x = (beam.start_point[0] + beam.end_point[0]) / 2
            mid_y = (beam.start_point[1] + beam.end_point[1]) / 2
            fig.add_annotation(
                x=mid_x, y=mid_y,
                text=f"{beam.id}<br>D={beam.depth:.0f}",
                showarrow=False,
                font=dict(size=7, color=color),
                bgcolor='rgba(255,255,255,0.7)'
            )
    
    # 4. 間柱の表示
    if show_layers.get("studs", True):
        for stud in structural_system.studs:
            color = LAYER_COLORS["S_COL"] if stud.stud_type == "king" else LAYER_COLORS["N_STUD"]
            width = 3 if stud.stud_type == "king" else 1
            
            # 間柱を短い線（ティック）で表示
            tick_length = 50  # mm
            fig.add_trace(go.Scatter(
                x=[stud.x, stud.x],
                y=[stud.y - tick_length/2, stud.y + tick_length/2],
                mode='lines',
                line=dict(color=color, width=width),
                name=f'間柱 {stud.id}',
                hovertemplate=f'間柱: {stud.id}<br>タイプ: {stud.stud_type}<br>{stud.note}<extra></extra>',
                showlegend=False
            ))
    
    # 5. 警告・違反の表示
    for warning in structural_system.warnings:
        # 警告箇所にマーカー表示（実装は簡略化）
        pass
    
    for violation in structural_system.violations:
        # 違反箇所にマーカー表示（実装は簡略化）
        pass
    
    fig.update_layout(
        title="構造平面図（柱・梁・間柱）",
        xaxis_title="X (mm)",
        yaxis_title="Y (mm)",
        showlegend=True,
        width=1000,
        height=800,
        xaxis=dict(scaleanchor="y", scaleratio=1),
        hovermode='closest'
    )
    
    return fig

def create_structural_3d_view(structural_system: StructuralSystem, project):
    """
    3D立体表示（構造要素）
    """
    fig = go.Figure()
    
    # 1. 柱の3D表示
    for col in structural_system.columns:
        color = LAYER_COLORS["LOCKED"] if col.locked else LAYER_COLORS["S_COL"]
        
        if col.section_type == "rect":
            # 矩形柱をメッシュで表示
            x0 = col.x - col.width / 2
            x1 = col.x + col.width / 2
            y0 = col.y - col.depth / 2
            y1 = col.y + col.depth / 2
            z0 = col.base_level
            z1 = col.top_level
            
            # 6面のメッシュ
            vertices_x = [x0, x1, x1, x0, x0, x1, x1, x0]
            vertices_y = [y0, y0, y1, y1, y0, y0, y1, y1]
            vertices_z = [z0, z0, z0, z0, z1, z1, z1, z1]
            
            # 面の定義（三角形）
            i = [0, 0, 4, 4, 0, 1, 1, 2, 2, 3, 3, 0]
            j = [1, 3, 5, 7, 4, 5, 2, 6, 3, 7, 0, 1]
            k = [2, 4, 6, 6, 5, 6, 6, 7, 7, 4, 4, 2]
            
            fig.add_trace(go.Mesh3d(
                x=vertices_x,
                y=vertices_y,
                z=vertices_z,
                i=i, j=j, k=k,
                color=color,
                opacity=0.7,
                name=f'柱 {col.id}',
                hovertemplate=f'柱: {col.id}<br>断面: {col.width:.0f}×{col.depth:.0f}<br>材質: {col.material}<extra></extra>'
            ))
    
    # 2. 梁の3D表示
    for beam in structural_system.beams:
        color = LAYER_COLORS["LINTEL"] if beam.is_lintel else LAYER_COLORS["S_BEAM"]
        if beam.locked:
            color = LAYER_COLORS["LOCKED"]
        
        # 梁を線分で表示（簡略化）
        fig.add_trace(go.Scatter3d(
            x=[beam.start_point[0], beam.end_point[0]],
            y=[beam.start_point[1], beam.end_point[1]],
            z=[beam.start_point[2], beam.end_point[2]],
            mode='lines',
            line=dict(color=color, width=5 if beam.is_lintel else 3),
            name=f'{"まぐさ" if beam.is_lintel else "梁"} {beam.id}',
            hovertemplate=f'{"まぐさ" if beam.is_lintel else "梁"}: {beam.id}<br>幅: {beam.width:.0f}mm<br>梁成: {beam.depth:.0f}mm<extra></extra>'
        ))
    
    # 3. 間柱の3D表示
    for stud in structural_system.studs:
        color = LAYER_COLORS["S_COL"] if stud.stud_type == "king" else LAYER_COLORS["N_STUD"]
        
        fig.add_trace(go.Scatter3d(
            x=[stud.x, stud.x],
            y=[stud.y, stud.y],
            z=[stud.base_level, stud.top_level],
            mode='lines',
            line=dict(color=color, width=3 if stud.stud_type == "king" else 1),
            name=f'間柱 {stud.id}',
            hovertemplate=f'間柱: {stud.id}<br>タイプ: {stud.stud_type}<extra></extra>',
            showlegend=False
        ))
    
    # 4. 頭上クリアランスの表示（2100mm面）
    clearance_height = 2100
    room_polygon = project.room.polygon
    
    x_coords = [p[0] for p in room_polygon]
    y_coords = [p[1] for p in room_polygon]
    z_coords = [clearance_height] * len(room_polygon)
    
    fig.add_trace(go.Mesh3d(
        x=x_coords,
        y=y_coords,
        z=z_coords,
        opacity=0.2,
        color='yellow',
        name='頭上クリアランス面 (2100mm)',
        hovertemplate='頭上クリアランス: 2100mm<extra></extra>'
    ))
    
    fig.update_layout(
        title="構造3D表示（柱・梁・間柱）",
        scene=dict(
            xaxis_title="X (mm)",
            yaxis_title="Y (mm)",
            zaxis_title="Z (mm)",
            aspectmode='data',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2)
            )
        ),
        width=1200,
        height=900,
        showlegend=True
    )
    
    return fig

def create_structural_section_view(structural_system: StructuralSystem, project, section_line: str = "X"):
    """
    断面図表示
    """
    fig = go.Figure()
    
    # 実装は簡略化（将来拡張）
    
    fig.update_layout(
        title=f"構造断面図（{section_line}方向）",
        xaxis_title="距離 (mm)",
        yaxis_title="高さ (mm)",
        width=1000,
        height=600
    )
    
    return fig
