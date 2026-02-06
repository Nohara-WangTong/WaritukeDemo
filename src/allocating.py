"""
建築的制約に基づく割付ロジック
"""
import time
import math
from typing import List, Tuple, Dict
from src.masterdata import Project, BoardMaster, Rules, Panel, StudGrid, Opening
from src.logic import place_opening_position

def generate_stud_grid(wall_length: float, stud_pitch: float = 455.0) -> StudGrid:
    """
    間柱グリッドの生成
    Args:
        wall_length: 壁の長さ（mm）
        stud_pitch: 間柱ピッチ（455mmまたは303mm）
    Returns:
        StudGrid: 間柱位置のリスト
    """
    positions = [0.0]  # 壁の左端から開始
    
    current_pos = 0.0
    while current_pos + stud_pitch < wall_length:
        current_pos += stud_pitch
        positions.append(current_pos)
    
    # 壁の右端を追加（ピッチの倍数でない場合も含む）
    if positions[-1] != wall_length:
        positions.append(wall_length)
    
    return StudGrid(positions=positions, pitch=stud_pitch)

def calculate_corner_winning_rules(polygon: List[Tuple[float, float]], wall_thickness: float) -> Dict:
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
        
        # 基本長さ
        if direction == "horizontal":
            base_length = abs(end[0] - start[0])
        else:
            base_length = abs(end[1] - start[1])
        
        # 勝ち負けに基づく調整
        # 各壁は隣接する2つの壁との関係で長さが決まる
        start_adjustment = 0.0
        end_adjustment = 0.0
        
        if wall_id == "W1":  # 横壁、両端で勝ち
            start_adjustment = 0.0  # W4に勝ち
            end_adjustment = 0.0    # W2に勝ち
            actual_length = base_length
        elif wall_id == "W2":  # 縦壁、下端で負け、上端で勝ち
            start_adjustment = wall_thickness  # W1に負け
            end_adjustment = 0.0               # W3に勝ち
            actual_length = base_length - wall_thickness
        elif wall_id == "W3":  # 横壁、右端で負け、左端で勝ち
            start_adjustment = 0.0             # W2に勝ち
            end_adjustment = wall_thickness    # W4に負け
            actual_length = base_length - wall_thickness
        else:  # W4: 縦壁、上端で負け、下端で勝ち
            start_adjustment = 0.0             # W3に勝ち
            end_adjustment = wall_thickness    # W1に負け
            actual_length = base_length - wall_thickness
        
        # 実際の開始・終了位置を計算
        if direction == "horizontal":
            if wall_id == "W1":
                actual_start = start
                actual_end = end
            else:  # W3
                actual_start = (start[0] - end_adjustment, start[1])
                actual_end = (end[0], end[1])
        else:  # vertical
            if wall_id == "W2":
                actual_start = (start[0], start[1] + start_adjustment)
                actual_end = end
            else:  # W4
                actual_start = start
                actual_end = (end[0], end[1] - end_adjustment)
        
        adjusted_walls[wall_id] = {
            "start": actual_start,
            "end": actual_end,
            "length": actual_length,
            "direction": direction,
            "base_length": base_length
        }
    
    return adjusted_walls

def clip_panel_by_openings(panel_rect: Tuple[float, float, float, float], 
                          openings: List[Opening], 
                          wall_length: float) -> List[Tuple[float, float, float, float]]:
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
        
        # 開口部の位置を計算
        off = place_opening_position(wall_length, opening)
        if opening.type == "door":
            oy0, oy1 = 0.0, opening.height
        else:
            oy0, oy1 = opening.sill_height, opening.sill_height + opening.height
        
        ox0, ox1 = off, off + opening.width
        
        for rect in result_rects:
            rx, ry, rw, rh = rect
            rx1, ry1 = rx + rw, ry + rh
            
            # 重なりチェック
            if not (rx1 <= ox0 or rx >= ox1 or ry1 <= oy0 or ry >= oy1):
                # 重なりがある場合、4方向に分割
                # 左側
                if rx < ox0:
                    new_rects.append((rx, ry, ox0 - rx, rh))
                # 右側
                if rx1 > ox1:
                    new_rects.append((ox1, ry, rx1 - ox1, rh))
                # 下側
                if ry < oy0:
                    new_rects.append((max(rx, ox0), ry, min(rx1, ox1) - max(rx, ox0), oy0 - ry))
                # 上側
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
                                                output_mode: str, stud_pitch: float = 455.0) -> Tuple[List[Panel], List[Dict]]:
    """
    建築的制約に基づく壁割付
    1. 間柱グリッドの生成
    2. ボードの配置（水平方向の決定）
    3. 開口部のクリッピング処理
    """
    t0 = time.perf_counter()
    panels: List[Panel] = []
    errors: List[Dict] = []
    
    # 出隅ルールを適用した壁情報を取得
    wall_info = calculate_corner_winning_rules(project.room.polygon, project.room.wall_thickness)
    H = project.room.height
    bw, bh = board.raw_width, board.raw_height  # 910, 1820 or 2430
    
    # 標準ボードサイズ
    standard_board_height = min(bh, H)  # 壁高さとボード高さの小さい方
    
    # 壁ごとの開口を準備
    openings_by_wall: Dict[str, List[Opening]] = {"W1":[], "W2":[], "W3":[], "W4":[]}
    for op in project.openings:
        if op.wall in openings_by_wall:
            openings_by_wall[op.wall].append(op)
    
    # 各壁の割付処理
    for wall_id in ["W1", "W2", "W3", "W4"]:
        wall = wall_info[wall_id]
        wall_length = wall["length"]
        wall_openings = openings_by_wall[wall_id]
        
        # 1. 間柱グリッドの生成
        stud_grid = generate_stud_grid(wall_length, stud_pitch)
        
        # 2. ボードの配置（水平方向）
        curr_x = 0.0
        
        while curr_x < wall_length - 1:  # 1mm未満は無視
            # 理想的な右端位置
            ideal_right = curr_x + bw  # 910mm
            
            # 間柱グリッド内で理想位置を超えない最大位置を探す
            next_x = curr_x
            for pos in stud_grid.positions:
                if pos > curr_x and pos <= ideal_right:
                    next_x = pos
                elif pos > ideal_right:
                    break
            
            # 見つからない場合は壁の端まで
            if next_x == curr_x:
                next_x = wall_length
            
            panel_width = next_x - curr_x
            
            # 最小片チェック
            if panel_width < rules.min_piece:
                errors.append({
                    "code": "E-004", 
                    "wall": wall_id, 
                    "msg": f"最小片違反: 幅={panel_width:.1f} < 最小片={rules.min_piece}"
                })
            
            # 3. 垂直方向の配置（高さ方向）
            curr_y = 0.0
            
            while curr_y < H - 1:  # 1mm未満は無視
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

def allocate_walls(project: Project, board: BoardMaster, rules: Rules, output_mode: str) -> Tuple[List[Panel], List[Dict]]:
    """
    建築的制約に基づく壁割付（メイン関数）
    """
    return allocate_walls_with_architectural_constraints(project, board, rules, output_mode)