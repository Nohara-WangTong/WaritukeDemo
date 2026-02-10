"""
入力データ処理
"""
from src.masterdata import Project, Room, Opening

def load_demo_project() -> Project:
    room = Room(
        room_id="R001",
        floor=1,
        use_type="居室",
        polygon=[(0,0),(7200,0),(7200,5400),(0,5400)],  # 倍のサイズ: 7200mm x 5400mm
        height=2400,
        wall_thickness=100
    )
    openings = [
        Opening(
            opening_id="O-D1",
            wall="W1",
            type="door",
            width=1500,
            height=2000,
            sill_height=0,
            offset_from_wall_start="910"  # 位置も調整
        ),
        Opening(
            opening_id="O-W1",
            wall="W3",
            type="window",
            width=1000,
            height=1000,
            sill_height=900,
            offset_from_wall_start="2000"  # 左寄りに配置
        ),
        Opening(
            opening_id="O-W2",
            wall="W3",
            type="window",
            width=1000,
            height=1000,
            sill_height=900,
            offset_from_wall_start="4200"  # 右寄りに配置
        )
    ]
    return Project(
        project_id="DEMO-0001",
        name="デモ案件（部屋1F + 扉1 + 窓2）",
        room=room,
        openings=openings
    )