"""
壁編集機能：マウス操作で壁を作成・編集
"""
from dataclasses import dataclass, replace
from typing import List, Tuple, Optional
import math

@dataclass
class WallSegment:
    """壁セグメント"""
    id: str
    start: Tuple[int, int]
    end: Tuple[int, int]
    thickness: int
    height: int
    is_new: bool = True  # 新規作成された壁かどうか

def snap_to_grid(point: Tuple[float, float], grid_size: int = 50) -> Tuple[int, int]:
    """座標をグリッドにスナップ"""
    x = round(point[0] / grid_size) * grid_size
    y = round(point[1] / grid_size) * grid_size
    return (int(x), int(y))

def snap_to_horizontal_or_vertical(start: Tuple[int, int], end: Tuple[int, int]) -> Tuple[int, int]:
    """線を水平または垂直にスナップ"""
    dx = abs(end[0] - start[0])
    dy = abs(end[1] - start[1])
    
    if dx > dy:
        # 水平線にスナップ
        return (end[0], start[1])
    else:
        # 垂直線にスナップ
        return (start[0], end[1])

def find_nearest_wall_point(point: Tuple[int, int], existing_walls: List[WallSegment], threshold: int = 100) -> Optional[Tuple[int, int]]:
    """既存の壁の端点または線上の最も近い点を見つける"""
    min_dist = float('inf')
    nearest_point = None
    
    for wall in existing_walls:
        # 始点との距離
        dist_start = math.sqrt((point[0] - wall.start[0])**2 + (point[1] - wall.start[1])**2)
        if dist_start < min_dist and dist_start < threshold:
            min_dist = dist_start
            nearest_point = wall.start
        
        # 終点との距離
        dist_end = math.sqrt((point[0] - wall.end[0])**2 + (point[1] - wall.end[1])**2)
        if dist_end < min_dist and dist_end < threshold:
            min_dist = dist_end
            nearest_point = wall.end
        
        # 線上の最も近い点
        # 線分のベクトル
        wall_vec = (wall.end[0] - wall.start[0], wall.end[1] - wall.start[1])
        wall_len_sq = wall_vec[0]**2 + wall_vec[1]**2
        
        if wall_len_sq > 0:
            # 点から線分への投影
            t = max(0, min(1, ((point[0] - wall.start[0]) * wall_vec[0] + 
                               (point[1] - wall.start[1]) * wall_vec[1]) / wall_len_sq))
            proj_x = wall.start[0] + t * wall_vec[0]
            proj_y = wall.start[1] + t * wall_vec[1]
            
            dist_proj = math.sqrt((point[0] - proj_x)**2 + (point[1] - proj_y)**2)
            if dist_proj < min_dist and dist_proj < threshold:
                min_dist = dist_proj
                nearest_point = (int(proj_x), int(proj_y))
    
    return nearest_point

def create_wall_from_line(start: Tuple[int, int], end: Tuple[int, int], 
                          wall_thickness: int, wall_height: int, 
                          existing_walls: List[WallSegment]) -> Optional[WallSegment]:
    """線から壁を作成（水平・垂直のみ）"""
    # 水平または垂直にスナップ
    snapped_end = snap_to_horizontal_or_vertical(start, end)
    
    # 既存の壁に接続
    snapped_start = find_nearest_wall_point(start, existing_walls) or start
    snapped_end = find_nearest_wall_point(snapped_end, existing_walls) or snapped_end
    
    # 最小長さチェック
    length = math.sqrt((snapped_end[0] - snapped_start[0])**2 + 
                      (snapped_end[1] - snapped_start[1])**2)
    if length < 100:  # 最小100mm
        return None
    
    # 壁IDを生成
    wall_id = f"W_NEW_{len(existing_walls) + 1}"
    
    return WallSegment(
        id=wall_id,
        start=snapped_start,
        end=snapped_end,
        thickness=wall_thickness,
        height=wall_height,
        is_new=True
    )

def create_walls_from_area(points: List[Tuple[int, int]], 
                           wall_thickness: int, wall_height: int,
                           existing_walls: List[WallSegment]) -> List[WallSegment]:
    """エリアから矩形の壁を作成"""
    if len(points) < 2:
        return []
    
    # バウンディングボックスを計算
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    
    # グリッドにスナップ
    min_x, min_y = snap_to_grid((min_x, min_y))
    max_x, max_y = snap_to_grid((max_x, max_y))
    
    # 最小サイズチェック
    if (max_x - min_x) < 500 or (max_y - min_y) < 500:  # 最小500mm
        return []
    
    # 矩形の4つの壁を作成
    corners = [
        (min_x, min_y),  # 左下
        (max_x, min_y),  # 右下
        (max_x, max_y),  # 右上
        (min_x, max_y),  # 左上
    ]
    
    walls = []
    base_id = len(existing_walls) + 1
    
    for i in range(4):
        start = corners[i]
        end = corners[(i + 1) % 4]
        
        # 既存の壁に接続
        snapped_start = find_nearest_wall_point(start, existing_walls) or start
        snapped_end = find_nearest_wall_point(end, existing_walls) or end
        
        wall_id = f"W_NEW_{base_id + i}"
        walls.append(WallSegment(
            id=wall_id,
            start=snapped_start,
            end=snapped_end,
            thickness=wall_thickness,
            height=wall_height,
            is_new=True
        ))
    
    return walls

def convert_walls_to_project_format(walls: List[WallSegment], project) -> List[Tuple[int, int]]:
    """壁セグメントをプロジェクトの多角形形式に変換"""
    # 既存の多角形を取得
    polygon = list(project.room.polygon)
    
    # 新しい壁を追加（簡略化：矩形のみサポート）
    # 実際の実装では、壁セグメントから閉じた多角形を構築する必要がある
    
    return polygon
