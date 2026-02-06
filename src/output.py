"""
出力・レポート生成機能
"""
import pandas as pd
from typing import List, Dict
from io import BytesIO
from src.masterdata import Panel, NestPlacement, BoardMaster

def df_panels(panels: List[Panel]) -> pd.DataFrame:
    rows = []
    for i, p in enumerate(panels, start=1):
        rows.append({
            "part_no": f"P{i:04d}",
            "wall": p.wall_id,
            "x0": round(p.x0,1),
            "y0": round(p.y0,1),
            "w": round(p.w,1),
            "h": round(p.h,1),
            "requires_cutout": p.requires_cutout,
            "is_cut_piece": p.is_cut_piece,
            "note": p.note
        })
    return pd.DataFrame(rows)

def df_errors(errors: List[Dict]) -> pd.DataFrame:
    return pd.DataFrame(errors)

def df_boards(placements: List[NestPlacement], board: BoardMaster) -> pd.DataFrame:
    rows = []
    for pl in placements:
        rows.append({
            "board_id": pl.sheet_id,
            "x": round(pl.x,1),
            "y": round(pl.y,1),
            "w": round(pl.w,1),
            "h": round(pl.h,1),
            "rotated": pl.rotated,
            "panel_ref": pl.panel_ref
        })
    return pd.DataFrame(rows)

def fig_to_png_bytes(fig) -> bytes:
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    buf.seek(0)
    return buf.read()