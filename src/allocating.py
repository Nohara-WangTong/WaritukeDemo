"""
建築的制約に基づく割付ロジック
外周壁（W1～W4）に加え、平面図エディタで作成した新規壁（内壁・間仕切り等）も割付対象。
内壁は片側面の割付（両面施工の場合は同一壁を2回割付する運用で対応可能）。
"""
import time
import math
from typing import List, Tuple, Dict, Optional, Any
from src.masterdata import Project, BoardMaster, Rules, Panel, StudGrid, Opening
from src.logic import place_opening_position


def extra_walls_to_wall_info(extra_walls: List[Any], start_id: int = 5) -> Dict[str, Dict]:
    """
    新規壁（WallSegment相当のリスト）を割付用の wall_info 形式に変換する。
    外周は出隅ルール済みのW1～W4、新規壁はW5, W6, ... として扱う（長さは実長、開口なし）。
    """
    result = {}
    for i, w in enumerate(extra_walls):
        wall_id = f"W{start_id + i}"
        start = getattr(w, "start", w.get("start") if isinstance(w, dict) else (0, 0))
        end = getattr(w, "end", w.get("end") if isinstance(w, dict) else (0, 0))
        length = int(round(math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)))
        direction = "horizontal" if abs(end[1] - start[1]) < abs(end[0] - start[0]) else "vertical"
        result[wall_id] = {
            "start": start,
            "end": end,
            "length": length,
            "direction": direction,
            "base_length": length,
        }
    return result

def generate_stud_grid(wall_length: int, stud_pitch: int = 455) -> StudGrid:
    """
    間柱グリッドの生成
    Args:
        wall_length: 壁の長さ（mm）
        stud_pitch: 間柱ピッチ（455 or 303 mm）
    Returns:
        StudGrid: 間柱位置のリスト（mm）
    """
    positions = [0]
    current_pos = 0
    while current_pos + stud_pitch < wall_length:
        current_pos += stud_pitch
        positions.append(current_pos)
    if positions[-1] != wall_length:
        positions.append(wall_length)
    return StudGrid(positions=positions, pitch=stud_pitch)

def calculate_corner_winning_rules(polygon: List[Tuple[int, int]], wall_thickness: int) -> Dict:
    """
    出隅の勝ち負けルールを適用（建築的に正しい実装）
    勝ち負けルール: 時計回りに W1→W2→W3→W4→W1 の順で勝ち
    勝ち側は通し、負け側は壁厚分だけ短くなる
    """
    walls = {
        "W1": {"start": polygon[0], "end": polygon[1], "direction": "horizontal", "wins_against": ["W4"], "loses_to": ["W2"]},
        "W2": {"start": polygon[1], "end": polygon[2], "direction": "vertical", "wins_against": ["W1"], "loses_to": ["W3"]},
        "W3": {"start": polygon[2], "end": polygon[3], "direction": "horizontal", "wins_against": ["W2"], "loses_to": ["W4"]},
        "W4": {"start": polygon[3], "end": polygon[0], "direction": "vertical", "wins_against": ["W3"], "loses_to": ["W1"]}
    }
    
    adjusted_walls = {}
    
    for wall_id, wall_info in walls.items():
        start = wall_info["start"]
        end = wall_info["end"]
        direction = wall_info["direction"]
        
        # 基本長さ（mm）
        if direction == "horizontal":
            base_length = abs(end[0] - start[0])
        else:
            base_length = abs(end[1] - start[1])
        start_adjustment = 0
        end_adjustment = 0
        if wall_id == "W1":
            actual_length = base_length
        elif wall_id == "W2":
            start_adjustment = wall_thickness
            actual_length = base_length - wall_thickness
        elif wall_id == "W3":
            end_adjustment = wall_thickness
            actual_length = base_length - wall_thickness
        else:  # W4
            end_adjustment = wall_thickness
            actual_length = base_length - wall_thickness
        # 実際の開始・終了位置（int）
        if direction == "horizontal":
            if wall_id == "W1":
                actual_start = start
                actual_end = end
            else:
                actual_start = (int(start[0] - end_adjustment), start[1])
                actual_end = end
        else:
            if wall_id == "W2":
                actual_start = (start[0], int(start[1] + start_adjustment))
                actual_end = end
            else:
                actual_start = start
                actual_end = (end[0], int(end[1] - end_adjustment))
        adjusted_walls[wall_id] = {
            "start": actual_start,
            "end": actual_end,
            "length": actual_length,
            "direction": direction,
            "base_length": base_length
        }
    
    return adjusted_walls

def clip_panel_by_openings(panel_rect: Tuple[int, int, int, int],
                          openings: List[Opening],
                          wall_length: int) -> List[Tuple[int, int, int, int]]:
    """
    パネルを開口部でクリッピング（矩形分割）
    Args:
        panel_rect: (x, y, width, height) パネルの矩形
        openings: 開口部のリスト
        wall_length: 壁の長さ
    Returns:
        List[Tuple]: クリッピング後の矩形リスト
    """
    px, py, pw, ph = panel_rect
    result_rects = [panel_rect]
    
    for opening in openings:
        new_rects = []
        
        off = place_opening_position(wall_length, opening)
        if opening.type == "door":
            oy0, oy1 = 0, opening.height
        else:
            oy0, oy1 = opening.sill_height, opening.sill_height + opening.height
        
        ox0, ox1 = off, off + opening.width
        
        for rect in result_rects:
            rx, ry, rw, rh = rect
            rx1, ry1 = rx + rw, ry + rh
            
            # 重なりチェック
            if not (rx1 <= ox0 or rx >= ox1 or ry1 <= oy0 or ry >= oy1):
                # 重なりがある場合、4方向に分割
                if rx < ox0:
                    new_rects.append((rx, ry, ox0 - rx, rh))
                if rx1 > ox1:
                    new_rects.append((ox1, ry, rx1 - ox1, rh))
                if ry < oy0:
                    new_rects.append((max(rx, ox0), ry, min(rx1, ox1) - max(rx, ox0), oy0 - ry))
                if ry1 > oy1:
                    new_rects.append((max(rx, ox0), oy1, min(rx1, ox1) - max(rx, ox0), ry1 - oy1))
            else:
                # 重なりがない場合はそのまま
                new_rects.append(rect)
        
        result_rects = new_rects
    
    # 面積が小さすぎる矩形を除去
    result_rects = [rect for rect in result_rects if rect[2] > 10 and rect[3] > 10]
    
    return result_rects

def allocate_walls_with_architectural_constraints(project: Project, board: BoardMaster, rules: Rules,
                                                output_mode: str, stud_pitch: int = 455,
                                                extra_walls: Optional[List[Any]] = None) -> Tuple[List[Panel], List[Dict]]:
    """
    建築的制約に基づく壁割付（外周W1～W4 + 新規壁W5,W6,...）
    1. 間柱グリッドの生成
    2. ボードの配置（水平方向の決定）
    3. 開口部のクリッピング処理（新規壁は開口なし）
    """
    t0 = time.perf_counter()
    panels: List[Panel] = []
    errors: List[Dict] = []
    
    wall_info = calculate_corner_winning_rules(project.room.polygon, project.room.wall_thickness)
    if extra_walls:
        extra_info = extra_walls_to_wall_info(extra_walls)
        wall_info = {**wall_info, **extra_info}
    
    H = project.room.height
    bw, bh = board.raw_width, board.raw_height
    
    standard_board_height = min(bh, H)
    
    wall_ids = list(wall_info.keys())
    openings_by_wall: Dict[str, List[Opening]] = {wid: [] for wid in wall_ids}
    for op in project.openings:
        if op.wall in openings_by_wall:
            openings_by_wall[op.wall].append(op)
    
    for wall_id in wall_ids:
        wall = wall_info[wall_id]
        wall_length = wall["length"]
        wall_openings = openings_by_wall[wall_id]
        
        # 1. 間柱グリッドの生成
        stud_grid = generate_stud_grid(wall_length, stud_pitch)
        
        curr_x = 0
        while curr_x < wall_length - 1:
            ideal_right = curr_x + bw
            next_x = curr_x
            for pos in stud_grid.positions:
                if pos > curr_x and pos <= ideal_right:
                    next_x = pos
                elif pos > ideal_right:
                    break
            if next_x == curr_x:
                next_x = wall_length
            panel_width = next_x - curr_x
            if panel_width < rules.min_piece:
                errors.append({
                    "code": "E-004",
                    "wall": wall_id,
                    "msg": f"最小片違反: 幅={panel_width} < 最小片={rules.min_piece}"
                })
            curr_y = 0
            while curr_y < H - 1:
                panel_height = min(standard_board_height, H - curr_y)
                
                # パネル矩形を作成
                panel_rect = (curr_x, curr_y, panel_width, panel_height)
                
                # 4. 開口部でクリッピング
                clipped_rects = clip_panel_by_openings(panel_rect, wall_openings, wall_length)
                
                # クリッピング結果をパネルとして登録
                for rect in clipped_rects:
                    rx, ry, rw, rh = rect
                    
                    # 端材判定
                    is_cut = (rw < bw - 1) or (rh < standard_board_height - 1)
                    requires_cutout = len([op for op in wall_openings 
                                         if not (rx + rw <= place_opening_position(wall_length, op) or 
                                               rx >= place_opening_position(wall_length, op) + op.width)]) > 0
                    
                    note = ""
                    if is_cut:
                        note = "端材"
                    if requires_cutout and not is_cut:
                        note = "要切欠"
                    
                    panel = Panel(
                        wall_id=wall_id,
                        x0=rx,
                        y0=ry,
                        w=rw,
                        h=rh,
                        requires_cutout=requires_cutout,
                        note=note,
                        is_cut_piece=is_cut,
                        original_size=(bw, standard_board_height)
                    )
                    panels.append(panel)
                
                curr_y += panel_height
            
            curr_x = next_x
    
    elapsed = time.perf_counter() - t0
    errors.append({"code":"INFO-TIME", "phase":"allocation", "sec": elapsed})
    
    return panels, errors

def allocate_walls(project: Project, board: BoardMaster, rules: Rules, output_mode: str,
                  stud_pitch: int = 455, extra_walls: Optional[List[Any]] = None) -> Tuple[List[Panel], List[Dict]]:
    """
    建築的制約に基づく壁割付（メイン関数）。extra_walls があれば W5,W6,... として追加割付。
    """
    return allocate_walls_with_architectural_constraints(
        project, board, rules, output_mode, stud_pitch, extra_walls
    )