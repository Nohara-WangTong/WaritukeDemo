"""
構造要素（柱・梁・間柱）の生成ロジック
"""
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
import math

@dataclass
class Column:
    """柱"""
    id: str
    x: int
    y: int
    base_level: int
    top_level: int
    section_type: str  # "rect" or "circle"
    width: int
    depth: int
    material: str
    is_virtual: bool = False
    locked: bool = False
    note: str = ""

@dataclass
class Beam:
    """梁"""
    id: str
    start_point: Tuple[int, int, int]  # (x, y, z) mm
    end_point: Tuple[int, int, int]
    width: int
    depth: int
    material: str
    is_lintel: bool = False
    opening_id: Optional[str] = None
    locked: bool = False
    note: str = ""

@dataclass
class Stud:
    """間柱"""
    id: str
    wall_id: str
    x: int
    y: int
    wall_position: int  # 壁の始点からの距離（mm）
    base_level: int
    top_level: int
    section_type: str
    width: int
    depth: int
    stud_type: str  # "regular", "king"
    opening_id: Optional[str] = None
    locked: bool = False
    note: str = ""

@dataclass
class GridLine:
    """通り芯"""
    id: str
    start_point: Tuple[int, int]
    end_point: Tuple[int, int]
    direction: str  # "X" or "Y"
    is_virtual: bool = False

@dataclass
class StructuralSystem:
    """構造システム全体"""
    columns: List[Column]
    beams: List[Beam]
    studs: List[Stud]
    grid_lines: List[GridLine]
    warnings: List[Dict]
    violations: List[Dict]

# 構造設計パラメータ
STRUCTURAL_PARAMS = {
    "RC": {
        "max_span": 8000,  # mm
        "min_column_size": 400,  # mm
        "typical_beam_depth": 600,  # mm
    },
    "S": {
        "max_span": 10000,  # mm
        "min_column_size": 300,  # mm
        "typical_beam_depth": 500,  # mm
    },
    "Wood": {
        "max_span": 6000,  # mm
        "min_column_size": 120,  # mm
        "typical_beam_depth": 300,  # mm
    }
}

# 間柱パラメータ
STUD_PARAMS = {
    "pitch_options": [303, 455, 610],  # mm
    "default_pitch": 455,
    "section_width": 89,  # mm (2x4材相当)
    "section_depth": 38,  # mm
    "min_clearance": 50,  # mm
    "lintel_clearance": 2100,  # mm
}

def generate_virtual_grid(room_polygon: List[Tuple[int, int]], material: str = "RC") -> List[GridLine]:
    """
    壁方向から仮想グリッドを推定
    """
    grid_lines = []
    max_span = STRUCTURAL_PARAMS[material]["max_span"]
    
    # 矩形の場合、X方向とY方向のグリッドを生成
    if len(room_polygon) == 4:
        # X方向のグリッド
        x_min = min(p[0] for p in room_polygon)
        x_max = max(p[0] for p in room_polygon)
        y_min = min(p[1] for p in room_polygon)
        y_max = max(p[1] for p in room_polygon)
        
        # X方向
        x_span = x_max - x_min
        num_x_grids = math.ceil(x_span / max_span) + 1
        x_spacing = x_span / (num_x_grids - 1) if num_x_grids > 1 else x_span
        
        for i in range(num_x_grids):
            x = int(x_min + i * x_spacing)
            grid_lines.append(GridLine(
                id=f"X{i+1}",
                start_point=(x, y_min),
                end_point=(x, y_max),
                direction="X",
                is_virtual=True
            ))
        y_span = y_max - y_min
        num_y_grids = math.ceil(y_span / max_span) + 1
        y_spacing = y_span / (num_y_grids - 1) if num_y_grids > 1 else y_span
        for i in range(num_y_grids):
            y = int(y_min + i * y_spacing)
            grid_lines.append(GridLine(
                id=f"Y{i+1}",
                start_point=(x_min, y),
                end_point=(x_max, y),
                direction="Y",
                is_virtual=True
            ))
    
    return grid_lines

def generate_columns_from_grid(grid_lines: List[GridLine], floor_height: int, material: str = "RC") -> List[Column]:
    """
    通り芯の交点に柱を生成
    """
    columns = []
    params = STRUCTURAL_PARAMS[material]
    
    # X方向とY方向のグリッドを分離
    x_grids = [g for g in grid_lines if g.direction == "X"]
    y_grids = [g for g in grid_lines if g.direction == "Y"]
    
    # 交点に柱を配置
    col_id = 1
    for x_grid in x_grids:
        for y_grid in y_grids:
            # 交点を計算
            x = x_grid.start_point[0]
            y = y_grid.start_point[1]
            
            # 柱を生成
            columns.append(Column(
                id=f"C{col_id:03d}",
                x=x,
                y=y,
                base_level=0,
                top_level=floor_height,
                section_type="rect",
                width=params["min_column_size"],
                depth=params["min_column_size"],
                material=material,
                is_virtual=x_grid.is_virtual or y_grid.is_virtual,
                note=f"Grid: {x_grid.id}-{y_grid.id}"
            ))
            col_id += 1
    
    return columns

def generate_beams_between_columns(columns: List[Column], material: str = "RC") -> List[Beam]:
    """
    柱間に梁を生成
    """
    beams = []
    params = STRUCTURAL_PARAMS[material]
    max_span = params["max_span"]
    beam_depth = params["typical_beam_depth"]
    beam_width = int(params["min_column_size"] * 0.6)  # 柱幅の60%程度
    
    beam_id = 1
    
    # 同じY座標の柱を接続（X方向の梁）
    y_groups = {}
    for col in columns:
        y_key = col.y
        if y_key not in y_groups:
            y_groups[y_key] = []
        y_groups[y_key].append(col)
    
    for y_key, cols in y_groups.items():
        cols_sorted = sorted(cols, key=lambda c: c.x)
        for i in range(len(cols_sorted) - 1):
            col1 = cols_sorted[i]
            col2 = cols_sorted[i + 1]
            span = abs(col2.x - col1.x)
            
            if span <= max_span:
                beams.append(Beam(
                    id=f"B{beam_id:03d}",
                    start_point=(col1.x, col1.y, col1.top_level),
                    end_point=(col2.x, col2.y, col2.top_level),
                    width=beam_width,
                    depth=beam_depth,
                    material=material,
                    note=f"Span: {span}mm"
                ))
                beam_id += 1
    x_groups = {}
    for col in columns:
        x_key = col.x
        if x_key not in x_groups:
            x_groups[x_key] = []
        x_groups[x_key].append(col)
    
    for x_key, cols in x_groups.items():
        cols_sorted = sorted(cols, key=lambda c: c.y)
        for i in range(len(cols_sorted) - 1):
            col1 = cols_sorted[i]
            col2 = cols_sorted[i + 1]
            span = abs(col2.y - col1.y)
            
            if span <= max_span:
                beams.append(Beam(
                    id=f"B{beam_id:03d}",
                    start_point=(col1.x, col1.y, col1.top_level),
                    end_point=(col2.x, col2.y, col2.top_level),
                    width=beam_width,
                    depth=beam_depth,
                    material=material,
                    note=f"Span: {span}mm"
                ))
                beam_id += 1
    return beams

def generate_lintels_for_openings(openings, wall_info: Dict, floor_height: int, material: str = "RC") -> Tuple[List[Beam], List[Dict]]:
    """
    開口上にまぐさを生成
    """
    lintels = []
    warnings = []
    params = STRUCTURAL_PARAMS[material]
    lintel_depth = int(params["typical_beam_depth"] * 0.5)
    lintel_width = 200
    
    lintel_id = 1
    
    for opening in openings:
        wall = wall_info.get(opening.wall)
        if not wall:
            continue
        
        # 開口上端の高さ
        if opening.type == "door":
            top_height = opening.height
        else:
            top_height = opening.sill_height + opening.height
        
        # 頭上クリアランスチェック
        clearance = floor_height - top_height - lintel_depth
        if clearance < STUD_PARAMS["lintel_clearance"]:
            warnings.append({
                "code": "W-CLEARANCE",
                "opening_id": opening.opening_id,
                "clearance": clearance,
                "required": STUD_PARAMS["lintel_clearance"],
                "message": f"開口 {opening.opening_id} の頭上クリアランス不足: {clearance}mm < {STUD_PARAMS['lintel_clearance']}mm"
            })
        
        if wall["direction"] == "horizontal":
            off = int(opening.offset_from_wall_start) if isinstance(opening.offset_from_wall_start, (int, float)) else (wall["length"] - opening.width) // 2
            start_x = wall["start"][0] + off
            end_x = start_x + opening.width
            y = wall["start"][1]
            lintels.append(Beam(
                id=f"L{lintel_id:03d}",
                start_point=(start_x, y, top_height),
                end_point=(end_x, y, top_height),
                width=lintel_width,
                depth=lintel_depth,
                material=material,
                is_lintel=True,
                opening_id=opening.opening_id,
                note=f"Lintel for {opening.opening_id}"
            ))
        else:
            off = int(opening.offset_from_wall_start) if isinstance(opening.offset_from_wall_start, (int, float)) else (wall["length"] - opening.width) // 2
            start_y = wall["start"][1] + off
            end_y = start_y + opening.width
            x = wall["start"][0]
            lintels.append(Beam(
                id=f"L{lintel_id:03d}",
                start_point=(x, start_y, top_height),
                end_point=(x, end_y, top_height),
                width=lintel_width,
                depth=lintel_depth,
                material=material,
                is_lintel=True,
                opening_id=opening.opening_id,
                note=f"Lintel for {opening.opening_id}"
            ))
        
        lintel_id += 1
    
    return lintels, warnings

def generate_studs_for_wall(wall_id: str, wall_info: Dict, openings, floor_height: int, pitch: int = 455) -> List[Stud]:
    """
    壁に間柱を生成（非耐力壁のみ）
    """
    studs = []
    wall = wall_info[wall_id]
    wall_length = wall["length"]
    
    # 開口部の位置を取得
    wall_openings = [op for op in openings if op.wall == wall_id]
    
    stud_id = 1
    current_x = 0
    
    while current_x <= wall_length:
        # 開口部との干渉チェック
        is_in_opening = False
        for opening in wall_openings:
            if isinstance(opening.offset_from_wall_start, (int, float)):
                op_start = int(opening.offset_from_wall_start)
            else:
                op_start = (wall_length - opening.width) // 2
            op_end = op_start + opening.width
            if op_start <= current_x <= op_end:
                is_in_opening = True
                break
        
        if not is_in_opening:
            if wall["direction"] == "horizontal":
                x = int(wall["start"][0] + (current_x / wall_length) * (wall["end"][0] - wall["start"][0]))
                y = wall["start"][1]
            else:
                x = wall["start"][0]
                y = int(wall["start"][1] + (current_x / wall_length) * (wall["end"][1] - wall["start"][1]))
            studs.append(Stud(
                id=f"ST_{wall_id}_{stud_id:03d}",
                wall_id=wall_id,
                x=x,
                y=y,
                wall_position=current_x,
                base_level=0,
                top_level=floor_height,
                section_type="C",
                width=STUD_PARAMS["section_width"],
                depth=STUD_PARAMS["section_depth"],
                stud_type="regular",
                note=f"@{pitch}mm"
            ))
            stud_id += 1
        
        current_x += pitch
    
    for opening in wall_openings:
        if isinstance(opening.offset_from_wall_start, (int, float)):
            op_start = int(opening.offset_from_wall_start)
        else:
            op_start = (wall_length - opening.width) // 2
        op_end = op_start + opening.width
        for pos, side in [(op_start, "left"), (op_end, "right")]:
            if wall["direction"] == "horizontal":
                x = int(wall["start"][0] + (pos / wall_length) * (wall["end"][0] - wall["start"][0]))
                y = wall["start"][1]
            else:
                x = wall["start"][0]
                y = int(wall["start"][1] + (pos / wall_length) * (wall["end"][1] - wall["start"][1]))
            studs.append(Stud(
                id=f"ST_{wall_id}_K{stud_id:03d}",
                wall_id=wall_id,
                x=x,
                y=y,
                wall_position=pos,
                base_level=0,
                top_level=floor_height,
                section_type="C",
                width=int(STUD_PARAMS["section_width"] * 1.5),
                depth=STUD_PARAMS["section_depth"],
                stud_type="king",
                opening_id=opening.opening_id,
                note=f"King stud ({side})"
            ))
            stud_id += 1
    
    return studs

def generate_structural_system(project, material: str = "RC", stud_pitch: int = 455) -> StructuralSystem:
    """
    構造システム全体を生成
    """
    from src.allocating import calculate_corner_winning_rules
    
    # 壁情報を取得
    wall_info = calculate_corner_winning_rules(project.room.polygon, project.room.wall_thickness)
    floor_height = project.room.height
    
    # 1. 仮想グリッドを生成
    grid_lines = generate_virtual_grid(project.room.polygon, material)
    
    # 2. グリッド交点に柱を生成
    columns = generate_columns_from_grid(grid_lines, floor_height, material)
    
    # 3. 柱間に梁を生成
    beams = generate_beams_between_columns(columns, material)
    
    # 4. 壁に間柱を生成（まぐさは生成しない）
    studs = []
    for wall_id in ["W1", "W2", "W3", "W4"]:
        wall_studs = generate_studs_for_wall(wall_id, wall_info, project.openings, floor_height, stud_pitch)
        studs.extend(wall_studs)
    
    # 5. 違反チェック
    violations = []
    warnings = []  # まぐさ生成を廃止したため警告は空
    
    # スパンチェック
    max_span = STRUCTURAL_PARAMS[material]["max_span"]
    for beam in beams:
        if not beam.is_lintel:
            span = math.sqrt(
                (beam.end_point[0] - beam.start_point[0])**2 +
                (beam.end_point[1] - beam.start_point[1])**2
            )
            if span > max_span:
                violations.append({
                    "code": "E-SPAN",
                    "beam_id": beam.id,
                    "span": span,
                    "max_span": max_span,
                    "message": f"梁 {beam.id} のスパン超過: {int(span)}mm > {max_span}mm"
                })
    
    return StructuralSystem(
        columns=columns,
        beams=beams,
        studs=studs,
        grid_lines=grid_lines,
        warnings=warnings,
        violations=violations
    )
