"""
マスターデータ定義
"""
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

@dataclass
class BoardMaster:
    name: str
    thickness: float
    raw_width: float
    raw_height: float
    rotatable: bool

@dataclass
class Rules:
    min_piece: float
    clearance: float
    kerf: float
    joint: float

@dataclass
class Room:
    room_id: str
    floor: int
    use_type: str
    polygon: List[Tuple[float, float]]  # [[x,y],...]
    height: float
    wall_thickness: float = 100.0  # 壁厚さ（mm）デフォルト100mm

@dataclass
class Opening:
    opening_id: str
    wall: str  # "W1","W2","W3","W4"
    type: str  # "door" | "window"
    width: float
    height: float
    sill_height: float
    offset_from_wall_start: str  # "center" or numeric in mm (string or float)

@dataclass
class Project:
    project_id: str
    name: str
    room: Room
    openings: List[Opening]

@dataclass
class Panel:
    wall_id: str      # W1..W4
    x0: float         # 壁起点からの横方向位置（mm）
    y0: float         # 床からの高さ（mm）
    w: float
    h: float
    requires_cutout: bool  # 開口の切欠が必要か
    note: str               # 備考（小片、違反など）
    is_cut_piece: bool = False  # 端材かどうか
    original_size: Tuple[float, float] = (910, 1820)  # 元の規格サイズ
    board_number: int = 0      # ボード番号（板取結果から設定）
    part_number: int = 0       # パーツ番号（板取結果から設定）

@dataclass
class StudGrid:
    """間柱グリッド情報"""
    positions: List[float]  # 間柱位置のリスト
    pitch: float           # 間柱ピッチ（455mmまたは303mm）

@dataclass
class NestPlacement:
    sheet_id: int
    x: float
    y: float
    w: float
    h: float
    rotated: bool
    panel_ref: Dict

def default_master() -> Tuple[BoardMaster, Rules, str]:
    board = BoardMaster(
        name="GB-R 3×8",
        thickness=12.5,
        raw_width=910,
        raw_height=2430,  # 3×8のデフォルト
        rotatable=True
    )
    rules = Rules(
        min_piece=150,
        clearance=5,
        kerf=3,
        joint=3
    )
    return board, rules, "セミ"  # output_mode