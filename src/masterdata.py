"""
マスターデータ定義
"""
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

@dataclass
class BoardMaster:
    name: str
    thickness: int       # mm
    raw_width: int       # mm
    raw_height: int      # mm
    rotatable: bool

@dataclass
class Rules:
    min_piece: int       # mm
    clearance: int       # mm
    kerf: int            # mm
    joint: int           # mm

@dataclass
class Room:
    room_id: str
    floor: int
    use_type: str
    polygon: List[Tuple[int, int]]  # [[x,y],...] mm
    height: int          # mm
    wall_thickness: int = 100  # 壁厚さ（mm）

@dataclass
class Opening:
    opening_id: str
    wall: str  # "W1","W2","W3","W4"
    type: str  # "door" | "window"
    width: int       # mm
    height: int      # mm
    sill_height: int # mm
    offset_from_wall_start: str  # "center" or numeric mm (string)

@dataclass
class Project:
    project_id: str
    name: str
    room: Room
    openings: List[Opening]

@dataclass
class Panel:
    wall_id: str      # W1..W4
    x0: int           # 壁起点からの横方向位置（mm）
    y0: int           # 床からの高さ（mm）
    w: int
    h: int
    requires_cutout: bool
    note: str
    is_cut_piece: bool = False
    original_size: Tuple[int, int] = (910, 2430)  # 元の規格サイズ（mm）
    board_number: int = 0
    part_number: int = 0

@dataclass
class StudGrid:
    """間柱グリッド情報"""
    positions: List[int]  # 間柱位置（mm）
    pitch: int            # 間柱ピッチ（455 or 303 mm）

@dataclass
class NestPlacement:
    sheet_id: int
    x: int
    y: int
    w: int
    h: int
    rotated: bool
    panel_ref: Dict

def default_master() -> Tuple[BoardMaster, Rules, str]:
    board = BoardMaster(
        name="GB-R 3×8",
        thickness=12,
        raw_width=910,
        raw_height=2430,
        rotatable=True
    )
    rules = Rules(
        min_piece=150,
        clearance=5,
        kerf=3,
        joint=3
    )
    return board, rules, "セミ"  # output_mode