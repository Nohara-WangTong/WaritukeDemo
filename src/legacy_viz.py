"""
従来の可視化（matplotlib版・互換性のため保持）
"""
from typing import List
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

from src.masterdata import Project, Panel, Opening, BoardMaster, NestPlacement
from src.logic import room_wall_lengths, place_opening_position

plt.rcParams["font.family"] = ["Meiryo", "MS Gothic", "Hiragino Sans", "Noto Sans CJK JP", "IPAexGothic", "Yu Gothic", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False


def plot_room_and_openings(project: Project):
    fig, ax = plt.subplots(figsize=(5, 5))
    poly = np.array(project.room.polygon + [project.room.polygon[0]])
    ax.plot(poly[:, 0], poly[:, 1], '-k', lw=2, label='部屋外形')
    cx = poly[:-1, 0].mean()
    cy = poly[:-1, 1].mean()
    ax.text(cx, cy, f"{project.name}\n{project.room.room_id}", ha='center', va='center', color='gray')

    wall_len = room_wall_lengths(project.room.polygon)
    origins = {
        "W1": project.room.polygon[0],
        "W2": project.room.polygon[1],
        "W3": project.room.polygon[2],
        "W4": project.room.polygon[3],
    }
    dirs = {"W1": (1, 0), "W2": (0, 1), "W3": (-1, 0), "W4": (0, -1)}
    colors = {"door": "tab:orange", "window": "tab:blue"}
    for op in project.openings:
        L = wall_len[op.wall]
        off = place_opening_position(L, op)
        ox = origins[op.wall][0] + off * dirs[op.wall][0]
        oy = origins[op.wall][1] + off * dirs[op.wall][1]
        ex = origins[op.wall][0] + (off + op.width) * dirs[op.wall][0]
        ey = origins[op.wall][1] + (off + op.width) * dirs[op.wall][1]
        ax.plot([ox, ex], [oy, ey], color=colors.get(op.type, 'tab:green'), lw=6, solid_capstyle='butt',
                label=f"{op.type}:{op.opening_id}")

    ax.set_aspect('equal', 'box')
    ax.set_title("平面図（部屋外形と開口の水平位置）")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.2)
    st.pyplot(fig)


def plot_wall_elevation(wall_id: str, wall_len: int, H: int, panels: List[Panel], openings: List[Opening], title: str):
    fig, ax = plt.subplots(figsize=(6, 3.2))
    ax.add_patch(plt.Rectangle((0, 0), wall_len, H, fill=False, ec='k', lw=1.5))
    for op in openings:
        off = place_opening_position(wall_len, op)
        if op.type == "door":
            oy0, oy1 = 0, op.height
        else:
            oy0, oy1 = op.sill_height, op.sill_height + op.height
        ax.add_patch(plt.Rectangle((off, oy0), op.width, oy1 - oy0, fill=True, alpha=0.25,
                                   color='tab:orange' if op.type == 'door' else 'tab:blue'))
        ax.text(off + op.width / 2, oy0 + (oy1 - oy0) / 2, op.opening_id, ha='center', va='center', fontsize=8)

    for p in panels:
        if p.wall_id != wall_id:
            continue
        fc = '#9bd3ff' if not p.requires_cutout else '#ffcf9b'
        ax.add_patch(plt.Rectangle((p.x0, p.y0), p.w, p.h, fill=True, alpha=0.6, ec='k', fc=fc))
        if p.note:
            ax.text(p.x0 + p.w / 2, p.y0 + p.h / 2, p.note, ha='center', va='center', fontsize=7)

    ax.set_xlim(-10, wall_len + 10)
    ax.set_ylim(0, H + 10)
    ax.set_title(title)
    ax.set_xlabel("壁方向 (mm)")
    ax.set_ylabel("高さ (mm)")
    ax.grid(True, alpha=0.2)
    st.pyplot(fig)


def plot_nesting(placements: List[NestPlacement], board: BoardMaster, utilization: float):
    if not placements:
        st.info("板取結果がありません。")
        return
    num_sheets = max(pl.sheet_id for pl in placements)
    for sid in range(1, num_sheets + 1):
        fig, ax = plt.subplots(figsize=(5, 8))
        ax.add_patch(plt.Rectangle((0, 0), board.raw_width, board.raw_height, fill=False, ec='k', lw=1.5))
        for pl in [p for p in placements if p.sheet_id == sid]:
            ax.add_patch(plt.Rectangle((pl.x, pl.y), pl.w, pl.h, fill=True, alpha=0.6, ec='k', fc='#c4f4c4'))
        ax.set_xlim(0, board.raw_width)
        ax.set_ylim(0, board.raw_height)
        ax.set_aspect('equal', 'box')
        ax.set_title(f"板取ボード #{sid}")
        ax.set_xlabel("X (mm)")
        ax.set_ylabel("Y (mm)")
        ax.grid(True, alpha=0.2)
        st.pyplot(fig)
    st.success(f"推定利用率（総合）: {utilization * 100:.1f}%")
