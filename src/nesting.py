"""
板取（2次元パッキング）ロジック
"""
import time
from dataclasses import asdict
from typing import List, Tuple
from src.masterdata import Panel, BoardMaster, Rules, NestPlacement

def simple_nesting(panels: List[Panel], board: BoardMaster, rules: Rules, prefer_y_long: bool) -> Tuple[List[NestPlacement], float, int]:
    """
    棚（Shelf）法による簡易板取。
    prefer_y_long=True で「長手優先（回転縮小）」のニュアンスを模擬（回転制限が強め）。
    戻り値: (placements, utilization, num_sheets)
    """
    t0 = time.perf_counter()

    W, H = board.raw_width, board.raw_height
    kerf = rules.kerf

    # 板候補（回転可の場合は (w,h) or (h,w) を状況に応じて使用）
    items = []
    for i, p in enumerate(panels):
        # 制約チェック：パーツが原板サイズを超えていないか
        if p.w > W or p.h > H:
            # 回転可能で回転すれば収まる場合
            if board.rotatable and p.h <= W and p.w <= H:
                items.append({
                    "w": p.h,  # 回転
                    "h": p.w,
                    "ref": asdict(p),
                    "panel_index": i,
                    "forced_rotation": True
                })
            else:
                print(f"警告: パーツ {p.w}×{p.h}mm は原板サイズを超えています")
                continue
        else:
            items.append({
                "w": p.w,
                "h": p.h,
                "ref": asdict(p),
                "panel_index": i,
                "forced_rotation": False
            })

    # 大きい順に並べる（面積降順）
    items.sort(key=lambda it: it["w"] * it["h"], reverse=True)

    placements: List[NestPlacement] = []
    sheet_id = 1
    shelf_y = 0.0
    shelf_height = 0.0
    cursor_x = 0.0
    part_counter = 1  # パーツ番号カウンター

    def new_sheet():
        nonlocal sheet_id, shelf_y, shelf_height, cursor_x, part_counter
        sheet_id += 1
        shelf_y = 0.0
        shelf_height = 0.0
        cursor_x = 0.0
        part_counter = 1  # 新しいボードでパーツ番号をリセット

    for it in items:
        w, h = it["w"], it["h"]
        panel_index = it["panel_index"]
        forced_rotation = it.get("forced_rotation", False)
        placed = False

        # 試す向きの順序：歩留り優先なら両方、長手優先なら回転制限
        if forced_rotation:
            orientations = [(w, h, True)]  # 強制回転
        else:
            orientations = [(w, h, False)]
            if board.rotatable and not prefer_y_long:
                orientations.append((h, w, True))

        for (tw, th, rotated) in orientations:
            # 制約チェック
            if tw > W or th > H:
                continue
                
            # 同じ棚（row）に入るか
            if cursor_x == 0.0:
                # 棚開始
                if tw <= W and shelf_y + th <= H:
                    # 元のパネルにボード番号とパーツ番号を設定
                    panels[panel_index].board_number = sheet_id
                    panels[panel_index].part_number = part_counter
                    
                    placements.append(NestPlacement(sheet_id, cursor_x, shelf_y, tw, th, rotated, it["ref"]))
                    cursor_x = tw + kerf
                    shelf_height = max(shelf_height, th + kerf)
                    part_counter += 1
                    placed = True
                    break
            else:
                if cursor_x + tw <= W and shelf_y + th <= H:
                    # 元のパネルにボード番号とパーツ番号を設定
                    panels[panel_index].board_number = sheet_id
                    panels[panel_index].part_number = part_counter
                    
                    placements.append(NestPlacement(sheet_id, cursor_x, shelf_y, tw, th, rotated, it["ref"]))
                    cursor_x += tw + kerf
                    shelf_height = max(shelf_height, th + kerf)
                    part_counter += 1
                    placed = True
                    break

        if not placed:
            # 新しい棚（次のrow）
            if shelf_y + shelf_height + h <= H:
                shelf_y += shelf_height
                shelf_height = 0.0
                cursor_x = 0.0
                # そのまま再試行（元向き優先）
                if forced_rotation:
                    orientations = [(w, h, True)]  # 強制回転
                else:
                    orientations = [(w, h, False)]
                    if board.rotatable and not prefer_y_long:
                        orientations.append((h, w, True))
                        
                placed2 = False
                for (tw, th, rotated) in orientations:
                    if tw <= W and shelf_y + th <= H:
                        # 元のパネルにボード番号とパーツ番号を設定
                        panels[panel_index].board_number = sheet_id
                        panels[panel_index].part_number = part_counter
                        
                        placements.append(NestPlacement(sheet_id, 0.0, shelf_y, tw, th, rotated, it["ref"]))
                        cursor_x = tw + kerf
                        shelf_height = max(shelf_height, th + kerf)
                        part_counter += 1
                        placed2 = True
                        break
                if not placed2:
                    # 新ボード
                    new_sheet()
                    # 元のパネルにボード番号とパーツ番号を設定
                    panels[panel_index].board_number = sheet_id
                    panels[panel_index].part_number = part_counter
                    
                    placements.append(NestPlacement(sheet_id, 0.0, 0.0, w, h, forced_rotation, it["ref"]))
                    cursor_x = w + kerf
                    shelf_height = h + kerf
                    part_counter += 1
            else:
                # 新ボード
                new_sheet()
                # 元のパネルにボード番号とパーツ番号を設定
                panels[panel_index].board_number = sheet_id
                panels[panel_index].part_number = part_counter
                
                placements.append(NestPlacement(sheet_id, 0.0, 0.0, w, h, forced_rotation, it["ref"]))
                cursor_x = w + kerf
                shelf_height = h + kerf
                part_counter += 1

    # 利用率
    used_area = sum(pl.w * pl.h for pl in placements)
    num_sheets = max(pl.sheet_id for pl in placements) if placements else 0
    total_area = num_sheets * W * H if num_sheets > 0 else 1.0
    utilization = used_area / total_area

    return placements, utilization, num_sheets