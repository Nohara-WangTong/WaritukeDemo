"""
基本的なロジック・ユーティリティ関数
"""
import math
from typing import List, Tuple, Dict
from src.masterdata import Opening

def room_wall_lengths(polygon: List[Tuple[int, int]]) -> Dict[str, int]:
    # 四角形前提：W1=(p0->p1), W2=(p1->p2), W3=(p2->p3), W4=(p3->p0)。長さは mm で int 返却。
    p = polygon
    lengths = {}
    def dist(a, b):
        return int(round(math.hypot(b[0] - a[0], b[1] - a[1])))
    lengths["W1"] = dist(p[0], p[1])
    lengths["W2"] = dist(p[1], p[2])
    lengths["W3"] = dist(p[2], p[3])
    lengths["W4"] = dist(p[3], p[0])
    return lengths


def place_opening_position(wall_len: int, opening: Opening) -> int:
    """壁起点からのオフセット（mm）を返す。center 指定に対応。"""
    if isinstance(opening.offset_from_wall_start, (int, float)):
        return int(opening.offset_from_wall_start)
    if isinstance(opening.offset_from_wall_start, str):
        s = opening.offset_from_wall_start.strip().lower()
        if s == "center":
            return (wall_len - opening.width) // 2
        try:
            return int(float(s))
        except (ValueError, TypeError):
            return 0
    return 0