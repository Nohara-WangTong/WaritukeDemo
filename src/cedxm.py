"""
CEDXM ファイル読み込み
Construction Exchange Data XML: 部屋情報を格納したXML形式
"""
import xml.etree.ElementTree as ET
from typing import Optional, Tuple
from src.masterdata import Project, Room, Opening, BoardMaster

# 石膏ボードサイズ: 割付高さで判断
# 高さ2420mm以下 → 3×8 (910×2430), 2730mm以下 → 3×9 (910×2730), それ以上 → 3×10 (910×3030)
BOARD_BY_HEIGHT = [
    (2420, "3×8", 910, 2430),
    (2730, "3×9", 910, 2730),
    (10000, "3×10", 910, 3030),
]


def get_board_for_height(wall_height_mm: int) -> Tuple[str, int, int]:
    """壁高さに応じた推奨石膏ボードサイズを返す (name, width, height) mm"""
    for max_h, name, w, h_val in BOARD_BY_HEIGHT:
        if wall_height_mm <= max_h:
            return (name, w, h_val)
    return ("3×10", 910, 3030)


def load_cedxm(content: str) -> Project:
    """
    CEDXM形式のXML文字列から Project を生成する
    """
    root = ET.fromstring(content)
    # CEDXM または Project をルートに想定
    proj_el = root.find(".//Project") or root
    if proj_el.tag != "Project":
        proj_el = root
    project_id = proj_el.get("id", "LOADED-01")
    project_name = proj_el.get("name", "CEDXM取込案件")

    room_el = proj_el.find("Room") or proj_el.find(".//Room")
    if room_el is None:
        raise ValueError("CEDXM: Room 要素が見つかりません")

    room_id = room_el.get("id", "R001")
    floor = int(room_el.get("floor", "1"))
    use_type = room_el.get("use_type", "居室")
    height = int(float(room_el.get("height", "2400")))
    wall_thickness = int(float(room_el.get("wall_thickness", "100")))

    polygon = []
    poly_el = room_el.find("Polygon") or room_el.find(".//Polygon")
    if poly_el is not None:
        for pt in poly_el.findall("Point"):
            x = int(float(pt.get("x", "0")))
            y = int(float(pt.get("y", "0")))
            polygon.append((x, y))
    if len(polygon) < 4:
        # デフォルト: 四角形
        polygon = [(0, 0), (3600, 0), (3600, 2700), (0, 2700)]

    openings = []
    openings_el = room_el.find("Openings") or room_el.find(".//Openings")
    if openings_el is not None:
        for op in openings_el.findall("Opening"):
            opening_id = op.get("id", f"O-{len(openings)+1}")
            wall = op.get("wall", "W1")
            otype = op.get("type", "door")
            width = int(float(op.get("width", "800")))
            oheight = int(float(op.get("height", "2000")))
            sill_height = int(float(op.get("sill_height", "0")))
            offset = op.get("offset", "center")
            openings.append(Opening(
                opening_id=opening_id,
                wall=wall,
                type=otype,
                width=width,
                height=oheight,
                sill_height=sill_height,
                offset_from_wall_start=offset
            ))

    room = Room(
        room_id=room_id,
        floor=floor,
        use_type=use_type,
        polygon=polygon,
        height=height,
        wall_thickness=wall_thickness
    )
    return Project(project_id=project_id, name=project_name, room=room, openings=openings)


def create_board_from_height(wall_height_mm: int) -> BoardMaster:
    """壁高さに応じた石膏ボードの BoardMaster を返す"""
    name, w, h = get_board_for_height(wall_height_mm)
    return BoardMaster(
        name=f"GB-R {name}",
        thickness=12,
        raw_width=w,
        raw_height=h,
        rotatable=True
    )
