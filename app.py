import time
import math
from dataclasses import dataclass, asdict
from typing import List, Tuple, Dict, Optional
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt

# 日本語フォントが□になる対策（Windows想定: Meiryo → MS Gothic → fallback）
plt.rcParams["font.family"] = ["Meiryo", "MS Gothic", "Hiragino Sans", "Noto Sans CJK JP", "IPAexGothic", "Yu Gothic", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False  # マイナス記号が文字化けしないようにする
from io import BytesIO

# 分割したモジュールのインポート
from src.masterdata import (
    BoardMaster, Rules, Room, Opening, Project, Panel, StudGrid, NestPlacement, 
    default_master
)
from src.input import load_demo_project
from src.logic import room_wall_lengths, place_opening_position
from src.allocating import (
    generate_stud_grid, calculate_corner_winning_rules, clip_panel_by_openings,
    allocate_walls_with_architectural_constraints, allocate_walls
)
from src.nesting import simple_nesting
from src.visualization import (
    create_room_plan_plotly, create_3d_elevation_view, 
    create_wall_elevation_plotly, create_nesting_plotly
)
from src.output import df_panels, df_errors, df_boards, fig_to_png_bytes

# =========================
# 多言語対応辞書
# =========================

LANGUAGES = {
    "日本語": "ja",
    "English": "en", 
    "中文": "zh",
    "Tiếng Việt": "vi"
}

TRANSLATIONS = {
    "ja": {
        # アプリタイトル・基本
        "app_title": "割付・板取 PoC",
        "app_subtitle": "割付・板取 PoC",
        "app_caption": "対象：四角部屋 + 扉1 + 窓1 / UI多言語対応・ロジックはPoC最小実装",
        
        # サイドバー
        "language_selection": "言語選択",
        "master_management": "マスター管理",
        "stud_pitch_setting": "間柱ピッチ設定",
        "stud_pitch": "間柱ピッチ",
        "board_size_selection": "板サイズ選択",
        "standard_board_size": "標準板サイズ",
        "allow_rotation": "回転を許可する",
        "standards_rules": "規格・ルール",
        "min_piece": "最小片 (mm)",
        "clearance": "クリアランス (mm)",
        "blade_thickness": "刃厚 (mm)",
        "joint_width": "ジョイント幅 (mm)",
        "output_format": "出力形態",
        "nesting_heuristics": "板取ルール",
        "processing_method": "加工方法",
        "yield_priority": "機械加工（歩留り優先）",
        "length_priority": "手加工（長手優先）",
        "execute_button": "▶ 割付・板取を実行",
        "execution_params": "実行パラメータ",
        
        # タブ
        "tab_project": "1. 案件ビュー",
        "tab_allocation": "2. 割付ビュー", 
        "tab_nesting": "3. 板取ビュー",
        "tab_drawings": "4. 図面・帳票ビュー",
        "tab_master": "5. マスター内容",
        
        # 案件ビュー
        "project_info": "案件情報",
        "project_id": "案件ID",
        "project_name": "案件名",
        "room": "部屋",
        "use_type": "用途",
        "floor": "階",
        "wall_height": "壁高さ",
        "opening_list": "開口一覧",
        "wall_info": "壁情報",
        "kpi_summary": "KPI サマリ",
        "yield_rate": "歩留まり（推定）",
        "sheet_count": "ボード枚数",
        "error_count": "エラー数",
        "plan_preview": "平面プレビュー（CAD図面）",
        "3d_elevation": "3D表示見付図",
        "3d_info": "3D表示を見るには、まず「割付・板取を実行」してください。",
        
        # 割付ビュー
        "wall_elevation": "壁立面・割付プレビュー（建築的制約対応）",
        "color_info": "色：緑=真物 / 青=端材 / 赤=開口部",
        "constraint_info": "※ 建築的制約: ボード配置は壁内側面、間柱グリッド（455mmピッチ）・出隅勝ち負けルール・開口部クリッピング処理を適用",
        "stud_setting": "間柱設定",
        "recalculate": "🔄 間柱ピッチを変更して再計算",
        "auto_fix": "🛠 最小片の一括自動修正（試作）",
        "recalculated": "で再計算しました。",
        "auto_fixed": "備考フラグを付与しました（PoC）。",
        
        # 板取ビュー
        "nesting_preview": "板取プレビュー",
        "utilization_rate": "推定利用率（総合）",
        "nesting_info": "板取結果を表示するには、まず「割付・板取を実行」してください。",
        
        # 図面・帳票ビュー
        "table_output": "表出力 / ダウンロード",
        "parts_table": "部材表（割付）",
        "download_parts": "部材表CSVをダウンロード",
        "sheet_layout": "ボード配置（板取）",
        "download_nesting": "板取結果CSVをダウンロード",
        "error_list": "エラー一覧",
        "download_errors": "エラーCSVをダウンロード",
        
        # マスタービュー
        "current_master": "現在のマスター設定",
        
        # フッター
        "footer_note1": "※ 本PoCは最小実装（四角部屋・矩形板・簡易分割）です。将来は板形状（切欠・角落とし）や詳細規則を拡張します。",
        "footer_note2": "※ CAD図面描画エンジンにPlotly（plotly.graph_objects、plotly.express、plotly.subplots）を使用し、インタラクティブな平面プレビューと3D表示見付図を実現しています。",
        
        # 実行メッセージ
        "execution_success": "建築的制約に基づく割付・板取を実行しました。（間柱ピッチ: {pitch:.0f}mm, 板サイズ: {board}）"
    },
    
    "en": {
        # App title & basic
        "app_title": "Panel Allocation & Nesting PoC",
        "app_subtitle": "Panel Allocation & Nesting PoC (Demo)",
        "app_caption": "Target: Rectangular room + 1 door + 1 window / Multi-language UI support, PoC minimal implementation logic",
        
        # Sidebar
        "language_selection": "Language Selection",
        "master_management": "Master Data Management",
        "stud_pitch_setting": "Stud Pitch Setting",
        "stud_pitch": "Stud Pitch",
        "board_size_selection": "Board Size Selection",
        "standard_board_size": "Standard Board Size",
        "allow_rotation": "Allow Rotation",
        "standards_rules": "Standards & Rules",
        "min_piece": "Min Piece (mm)",
        "clearance": "Clearance (mm)",
        "blade_thickness": "Blade Thickness (mm)",
        "joint_width": "Joint Width (mm)",
        "output_format": "Output Format",
        "nesting_heuristics": "Nesting Heuristics",
        "processing_method": "Processing Method Preference",
        "yield_priority": "Yield Priority (Allow Rotation)",
        "length_priority": "Length Priority (Restrict Rotation)",
        "execute_button": "▶ Execute Allocation & Nesting",
        "execution_params": "Execution Parameters",
        
        # Tabs
        "tab_project": "1. Project View",
        "tab_allocation": "2. Allocation View",
        "tab_nesting": "3. Nesting View",
        "tab_drawings": "4. Drawings & Reports View",
        "tab_master": "5. Master Data",
        
        # Project view
        "project_info": "Project Information",
        "project_id": "Project ID",
        "project_name": "Project Name",
        "room": "Room",
        "use_type": "Use Type",
        "floor": "Floor",
        "wall_height": "Wall Height",
        "opening_list": "Opening List",
        "wall_info": "Wall Information (After Corner Rules Applied)",
        "kpi_summary": "KPI Summary (PoC)",
        "yield_rate": "Yield Rate (Estimated)",
        "sheet_count": "Board Count",
        "error_count": "Error Count",
        "plan_preview": "Plan Preview (CAD Drawing Engine)",
        "3d_elevation": "3D Elevation View",
        "3d_info": "To view 3D display, please execute 'Allocation & Nesting' first.",
        
        # Allocation view
        "wall_elevation": "Wall Elevation & Allocation Preview (Architectural Constraints)",
        "color_info": "Colors: Light Green=Good Pieces / Light Blue=Semi/Full/Cut Pieces / Dark Red=Openings",
        "constraint_info": "※ Architectural Constraints: Board placement on interior wall surfaces, Stud Grid (455mm pitch), Corner Winning Rules, Opening Clipping Applied",
        "stud_setting": "Stud Setting",
        "recalculate": "🔄 Recalculate with Changed Stud Pitch",
        "auto_fix": "🛠 Auto Fix Min Pieces (Prototype)",
        "recalculated": "recalculated.",
        "auto_fixed": "Remark flags added (PoC).",
        
        # Nesting view
        "nesting_preview": "Nesting Preview",
        "utilization_rate": "Estimated Utilization Rate (Overall)",
        "nesting_info": "To display nesting results, please execute 'Allocation & Nesting' first.",
        
        # Drawings & reports view
        "table_output": "Table Output / Download",
        "parts_table": "Parts Table (Allocation)",
        "download_parts": "Download Parts CSV",
        "sheet_layout": "Board Layout (Nesting)",
        "download_nesting": "Download Nesting CSV",
        "error_list": "Error List",
        "download_errors": "Download Errors CSV",
        
        # Master view
        "current_master": "Current Master Settings",
        
        # Footer
        "footer_note1": "※ This PoC is minimal implementation (rectangular room, rectangular board, simple division). Future versions will expand board shapes (notches, corner cuts) and detailed rules.",
        "footer_note2": "※ CAD drawing engine uses Plotly (plotly.graph_objects, plotly.express, plotly.subplots) to achieve interactive plan preview and 3D elevation view.",
        
        # Execution messages
        "execution_success": "Executed allocation & nesting based on architectural constraints. (Stud pitch: {pitch:.0f}mm, Board size: {board})"
    },
    
    "zh": {
        # 应用标题和基本信息
        "app_title": "板材分配与排料 PoC",
        "app_subtitle": "板材分配与排料 PoC（演示）",
        "app_caption": "目标：矩形房间 + 1门 + 1窗 / 多语言UI支持，PoC最小实现逻辑",
        
        # 侧边栏
        "language_selection": "语言选择",
        "master_management": "主数据管理",
        "stud_pitch_setting": "龙骨间距设置",
        "stud_pitch": "龙骨间距",
        "board_size_selection": "板材尺寸选择",
        "standard_board_size": "标准板材尺寸",
        "allow_rotation": "允许旋转",
        "standards_rules": "标准与规则",
        "min_piece": "最小片 (mm)",
        "clearance": "间隙 (mm)",
        "blade_thickness": "刀厚 (mm)",
        "joint_width": "接缝宽度 (mm)",
        "output_format": "输出格式",
        "nesting_heuristics": "排料启发式",
        "processing_method": "加工方法偏好",
        "yield_priority": "收率优先（允许旋转）",
        "length_priority": "长度优先（限制旋转）",
        "execute_button": "▶ 执行分配与排料",
        "execution_params": "执行参数",
        
        # 标签页
        "tab_project": "1. 项目视图",
        "tab_allocation": "2. 分配视图",
        "tab_nesting": "3. 排料视图",
        "tab_drawings": "4. 图纸与报表视图",
        "tab_master": "5. 主数据",
        
        # 项目视图
        "project_info": "项目信息",
        "project_id": "项目ID",
        "project_name": "项目名称",
        "room": "房间",
        "use_type": "用途类型",
        "floor": "楼层",
        "wall_height": "墙高",
        "opening_list": "开口列表",
        "wall_info": "墙体信息（应用转角规则后）",
        "kpi_summary": "KPI摘要（PoC）",
        "yield_rate": "收率（估计）",
        "sheet_count": "板材数量",
        "error_count": "错误数量",
        "plan_preview": "平面预览（CAD绘图引擎）",
        "3d_elevation": "3D立面视图",
        "3d_info": "要查看3D显示，请先执行\"分配与排料\"。",
        
        # 分配视图
        "wall_elevation": "墙体立面与分配预览（建筑约束）",
        "color_info": "颜色：浅绿色=真物 / 浅蓝色=半成品/全成品/切割片 / 深红色=开口部",
        "constraint_info": "※ 建筑约束：板材配置在墙体内侧面，龙骨网格（455mm间距）、转角胜负规则、开口裁剪处理已应用",
        "stud_setting": "龙骨设置",
        "recalculate": "🔄 更改龙骨间距并重新计算",
        "auto_fix": "🛠 最小片自动修复（原型）",
        "recalculated": "重新计算完成。",
        "auto_fixed": "已添加备注标志（PoC）。",
        
        # 排料视图
        "nesting_preview": "排料预览",
        "utilization_rate": "估计利用率（总体）",
        "nesting_info": "要显示排料结果，请先执行\"分配与排料\"。",
        
        # 图纸与报表视图
        "table_output": "表格输出 / 下载",
        "parts_table": "零件表（分配）",
        "download_parts": "下载零件CSV",
        "sheet_layout": "板材布局（排料）",
        "download_nesting": "下载排料CSV",
        "error_list": "错误列表",
        "download_errors": "下载错误CSV",
        
        # 主数据视图
        "current_master": "当前主数据设置",
        
        # 页脚
        "footer_note1": "※ 此PoC为最小实现（矩形房间、矩形板材、简单分割）。未来版本将扩展板材形状（缺口、倒角）和详细规则。",
        "footer_note2": "※ CAD绘图引擎使用Plotly（plotly.graph_objects、plotly.express、plotly.subplots）实现交互式平面预览和3D立面视图。",
        
        # 执行消息
        "execution_success": "基于建筑约束执行分配与排料完成。（龙骨间距：{pitch:.0f}mm，板材尺寸：{board}）"
    },
    
    "vi": {
        # Tiêu đề ứng dụng và thông tin cơ bản
        "app_title": "Phân bổ & Sắp xếp Tấm PoC",
        "app_subtitle": "Phân bổ & Sắp xếp Tấm PoC (Demo)",
        "app_caption": "Mục tiêu: Phòng chữ nhật + 1 cửa + 1 cửa sổ / Hỗ trợ UI đa ngôn ngữ, logic triển khai tối thiểu PoC",
        
        # Thanh bên
        "language_selection": "Chọn Ngôn ngữ",
        "master_management": "Quản lý Dữ liệu Chính",
        "stud_pitch_setting": "Cài đặt Khoảng cách Cột",
        "stud_pitch": "Khoảng cách Cột",
        "board_size_selection": "Chọn Kích thước Tấm",
        "standard_board_size": "Kích thước Tấm Tiêu chuẩn",
        "allow_rotation": "Cho phép Xoay",
        "standards_rules": "Tiêu chuẩn & Quy tắc",
        "min_piece": "Mảnh Tối thiểu (mm)",
        "clearance": "Khoảng hở (mm)",
        "blade_thickness": "Độ dày Lưỡi cắt (mm)",
        "joint_width": "Độ rộng Mối nối (mm)",
        "output_format": "Định dạng Đầu ra",
        "nesting_heuristics": "Thuật toán Sắp xếp",
        "processing_method": "Ưu tiên Phương pháp Gia công",
        "yield_priority": "Ưu tiên Hiệu suất (Cho phép Xoay)",
        "length_priority": "Ưu tiên Chiều dài (Hạn chế Xoay)",
        "execute_button": "▶ Thực hiện Phân bổ & Sắp xếp",
        "execution_params": "Tham số Thực hiện",
        
        # Các tab
        "tab_project": "1. Xem Dự án",
        "tab_allocation": "2. Xem Phân bổ",
        "tab_nesting": "3. Xem Sắp xếp",
        "tab_drawings": "4. Xem Bản vẽ & Báo cáo",
        "tab_master": "5. Dữ liệu Chính",
        
        # Xem dự án
        "project_info": "Thông tin Dự án",
        "project_id": "ID Dự án",
        "project_name": "Tên Dự án",
        "room": "Phòng",
        "use_type": "Loại Sử dụng",
        "floor": "Tầng",
        "wall_height": "Chiều cao Tường",
        "opening_list": "Danh sách Lỗ mở",
        "wall_info": "Thông tin Tường (Sau khi áp dụng Quy tắc Góc)",
        "kpi_summary": "Tóm tắt KPI (PoC)",
        "yield_rate": "Tỷ lệ Hiệu suất (Ước tính)",
        "sheet_count": "Số lượng Tấm",
        "error_count": "Số lượng Lỗi",
        "plan_preview": "Xem trước Mặt bằng (Công cụ Vẽ CAD)",
        "3d_elevation": "Xem Mặt đứng 3D",
        "3d_info": "Để xem hiển thị 3D, vui lòng thực hiện 'Phân bổ & Sắp xếp' trước.",
        
        # Xem phân bổ
        "wall_elevation": "Mặt đứng Tường & Xem trước Phân bổ (Ràng buộc Kiến trúc)",
        "color_info": "Màu sắc: Xanh nhạt=Mảnh Tốt / Xanh dương nhạt=Mảnh Bán/Đầy/Cắt / Đỏ đậm=Lỗ mở",
        "constraint_info": "※ Ràng buộc Kiến trúc: Vị trí tấm ở mặt trong tường, Lưới Cột (khoảng cách 455mm), Quy tắc Thắng thua Góc, Xử lý Cắt Lỗ mở đã được áp dụng",
        "stud_setting": "Cài đặt Cột",
        "recalculate": "🔄 Thay đổi Khoảng cách Cột và Tính lại",
        "auto_fix": "🛠 Tự động Sửa Mảnh Tối thiểu (Nguyên mẫu)",
        "recalculated": "đã được tính lại.",
        "auto_fixed": "Đã thêm cờ ghi chú (PoC).",
        
        # Xem sắp xếp
        "nesting_preview": "Xem trước Sắp xếp (Phiên bản Plotly)",
        "utilization_rate": "Tỷ lệ Sử dụng Ước tính (Tổng thể)",
        "nesting_info": "Để hiển thị kết quả sắp xếp, vui lòng thực hiện 'Phân bổ & Sắp xếp' trước.",
        
        # Xem bản vẽ & báo cáo
        "table_output": "Đầu ra Bảng / Tải xuống",
        "parts_table": "Bảng Chi tiết (Phân bổ)",
        "download_parts": "Tải xuống CSV Chi tiết",
        "sheet_layout": "Bố cục Tấm (Sắp xếp)",
        "download_nesting": "Tải xuống CSV Sắp xếp",
        "error_list": "Danh sách Lỗi",
        "download_errors": "Tải xuống CSV Lỗi",
        
        # Xem dữ liệu chính
        "current_master": "Cài đặt Dữ liệu Chính Hiện tại",
        
        # Chân trang
        "footer_note1": "※ PoC này là triển khai tối thiểu (phòng chữ nhật, tấm chữ nhật, phân chia đơn giản). Các phiên bản tương lai sẽ mở rộng hình dạng tấm (rãnh, cắt góc) và quy tắc chi tiết.",
        "footer_note2": "※ Công cụ vẽ CAD sử dụng Plotly (plotly.graph_objects, plotly.express, plotly.subplots) để đạt được xem trước mặt bằng tương tác và xem mặt đứng 3D.",
        
        # Thông báo thực hiện
        "execution_success": "Đã thực hiện phân bổ & sắp xếp dựa trên ràng buộc kiến trúc. (Khoảng cách cột: {pitch:.0f}mm, Kích thước tấm: {board})"
    }
}

def get_text(key: str, lang: str = "ja") -> str:
    """多言語テキストを取得する関数"""
    return TRANSLATIONS.get(lang, TRANSLATIONS["ja"]).get(key, key)

# =========================
# 従来の可視化（matplotlib版 - 互換性のため保持）
# =========================

def plot_room_and_openings(project: Project):
    fig, ax = plt.subplots(figsize=(5,5))
    poly = np.array(project.room.polygon + [project.room.polygon[0]])
    ax.plot(poly[:,0], poly[:,1], '-k', lw=2, label='部屋外形')
    # 壁ラベル
    cx = poly[:-1,0].mean()
    cy = poly[:-1,1].mean()
    ax.text(cx, cy, f"{project.name}\n{project.room.room_id}", ha='center', va='center', color='gray')

    # 開口可視化（平面上は壁上の線分として簡略）
    wall_len = room_wall_lengths(project.room.polygon)
    origins = {
        "W1": project.room.polygon[0],  # (0,0) -> (L,0)
        "W2": project.room.polygon[1],  # (L,0) -> (L,W)
        "W3": project.room.polygon[2],  # (L,W) -> (0,W)
        "W4": project.room.polygon[3],  # (0,W) -> (0,0)
    }
    dirs = {
        "W1": (1,0),
        "W2": (0,1),
        "W3": (-1,0),
        "W4": (0,-1)
    }
    colors = {"door":"tab:orange", "window":"tab:blue"}
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
    ax.set_xlabel("X (mm)"); ax.set_ylabel("Y (mm)")
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.2)
    st.pyplot(fig)

def plot_wall_elevation(wall_id: str, wall_len: float, H: float, panels: List[Panel], openings: List[Opening], title: str):
    fig, ax = plt.subplots(figsize=(6,3.2))
    # 壁長方形
    ax.add_patch(plt.Rectangle((0,0), wall_len, H, fill=False, ec='k', lw=1.5))
    # 開口（投影）
    for op in openings:
        off = place_opening_position(wall_len, op)
        if op.type == "door":
            oy0, oy1 = 0.0, op.height
        else:
            oy0, oy1 = op.sill_height, op.sill_height + op.height
        ax.add_patch(plt.Rectangle((off, oy0), op.width, oy1-oy0, fill=True, alpha=0.25,
                                   color='tab:orange' if op.type=='door' else 'tab:blue'))
        ax.text(off+op.width/2, oy0+(oy1-oy0)/2, op.opening_id, ha='center', va='center', fontsize=8)

    # パネル
    for p in panels:
        if p.wall_id != wall_id: 
            continue
        fc = '#9bd3ff' if not p.requires_cutout else '#ffcf9b'
        ax.add_patch(plt.Rectangle((p.x0, p.y0), p.w, p.h, fill=True, alpha=0.6, ec='k', fc=fc))
        if p.note:
            ax.text(p.x0+p.w/2, p.y0+p.h/2, p.note, ha='center', va='center', fontsize=7)

    ax.set_xlim(-10, wall_len+10)
    ax.set_ylim(0, H+10)
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
    for sid in range(1, num_sheets+1):
        fig, ax = plt.subplots(figsize=(5,8))
        ax.add_patch(plt.Rectangle((0,0), board.raw_width, board.raw_height, fill=False, ec='k', lw=1.5))
        for pl in [p for p in placements if p.sheet_id == sid]:
            ax.add_patch(plt.Rectangle((pl.x, pl.y), pl.w, pl.h, fill=True, alpha=0.6, ec='k', fc='#c4f4c4'))
        ax.set_xlim(0, board.raw_width)
        ax.set_ylim(0, board.raw_height)
        ax.set_aspect('equal', 'box')
        ax.set_title(f"板取ボード #{sid}")
        ax.set_xlabel("X (mm)"); ax.set_ylabel("Y (mm)")
        ax.grid(True, alpha=0.2)
        st.pyplot(fig)
    st.success(f"推定利用率（総合）: {utilization*100:.1f}%")

# =========================
# Streamlit アプリ
# =========================

st.set_page_config(page_title="Panel Allocation & Nesting PoC", layout="wide")

# セッション状態の初期化
if "project" not in st.session_state:
    st.session_state.project = load_demo_project()
if "board" not in st.session_state:
    b, r, mode = default_master()
    st.session_state.board = b
    st.session_state.rules = r
    st.session_state.output_mode = mode
if "results" not in st.session_state:
    st.session_state.results = {}
if "language" not in st.session_state:
    st.session_state.language = "ja"  # デフォルト言語

# 現在の言語を取得
current_lang = st.session_state.language

st.title(get_text("app_title", current_lang))
st.caption(get_text("app_caption", current_lang))

# === サイドバー（言語選択を最上部に追加） ===
with st.sidebar:
    # 言語選択（最上部）
    st.subheader(get_text("language_selection", current_lang))
    selected_language = st.selectbox(
        "",  # ラベルを空にして、subheaderをラベルとして使用
        options=list(LANGUAGES.keys()),
        index=list(LANGUAGES.values()).index(current_lang),
        key="language_selector"
    )
    
    # 言語が変更された場合、セッション状態を更新
    if LANGUAGES[selected_language] != current_lang:
        st.session_state.language = LANGUAGES[selected_language]
        # Streamlit v1.36+ では experimental_rerun が廃止され st.rerun() に統合
        st.rerun()
    
    st.divider()  # 言語選択と他の設定を区切る
    
    st.header(get_text("master_management", current_lang))
    
    st.subheader(get_text("stud_pitch_setting", current_lang))
    stud_pitch = st.selectbox(get_text("stud_pitch", current_lang), [455.0, 303.0], index=0, format_func=lambda x: f"{x:.0f}mm")
    
    st.subheader(get_text("board_size_selection", current_lang))
    board_options = {
        "3×8 (910×2430mm)": (910, 2430),
        "3×9 (910×2730mm)": (910, 2730), 
        "3×10 (910×3030mm)": (910, 3030)
    }
    selected_board = st.selectbox(get_text("standard_board_size", current_lang), list(board_options.keys()), index=0)
    bw_new, bh_new = board_options[selected_board]
    
    # 板サイズが変更された場合の更新
    if st.session_state.board.raw_width != bw_new or st.session_state.board.raw_height != bh_new:
        st.session_state.board.raw_width = bw_new
        st.session_state.board.raw_height = bh_new
        st.session_state.board.name = f"GB-R {selected_board.split()[0]}"

    rot = st.checkbox(get_text("allow_rotation", current_lang), value=st.session_state.board.rotatable)
    st.session_state.board.rotatable = rot

    st.subheader(get_text("standards_rules", current_lang))
    st.session_state.rules.min_piece = st.number_input(get_text("min_piece", current_lang), value=float(st.session_state.rules.min_piece), min_value=10.0, step=10.0)
    st.session_state.rules.clearance = st.number_input(get_text("clearance", current_lang), value=float(st.session_state.rules.clearance), min_value=0.0, step=1.0)
    st.session_state.rules.kerf = st.number_input(get_text("blade_thickness", current_lang), value=float(st.session_state.rules.kerf), min_value=0.0, step=0.5)
    st.session_state.rules.joint = st.number_input(get_text("joint_width", current_lang), value=float(st.session_state.rules.joint), min_value=0.0, step=0.5)

    st.subheader(get_text("output_format", current_lang))
    output_options = ["真物","セミ","フル"] if current_lang == "ja" else ["Good","Semi","Full"]
    _mode = st.session_state.output_mode if st.session_state.output_mode != "良物" else "真物"
    current_index = ["真物","セミ","フル"].index(_mode)
    st.session_state.output_mode = st.radio("", output_options, index=current_index, horizontal=True)
    # 内部的には日本語の値を保持
    if current_lang != "ja":
        mode_mapping = {"Good": "真物", "Semi": "セミ", "Full": "フル"}
        st.session_state.output_mode = mode_mapping.get(st.session_state.output_mode, st.session_state.output_mode)

    st.subheader(get_text("nesting_heuristics", current_lang))
    prefer_y_long = st.radio(
        get_text("processing_method", current_lang), 
        [get_text("yield_priority", current_lang), get_text("length_priority", current_lang)], 
        index=1, 
        horizontal=False
    ) == get_text("length_priority", current_lang)

    run = st.button(get_text("execute_button", current_lang))
    
    # 実行時のパラメータ表示
    if run:
        st.write(f"{get_text('execution_params', current_lang)}: {get_text('standard_board_size', current_lang)}={selected_board}, {get_text('stud_pitch', current_lang)}={stud_pitch:.0f}mm")

# === メイン：タブ ===
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    get_text("tab_project", current_lang),
    get_text("tab_allocation", current_lang), 
    get_text("tab_nesting", current_lang),
    get_text("tab_drawings", current_lang),
    get_text("tab_master", current_lang)
])

project: Project = st.session_state.project
board: BoardMaster = st.session_state.board
rules: Rules = st.session_state.rules
output_mode: str = st.session_state.output_mode

# 実行
if run:
    # 割付（建築的制約対応）
    panels, errors = allocate_walls_with_architectural_constraints(project, board, rules, output_mode, stud_pitch)
    # 板取
    placements, util, num_sheets = simple_nesting(panels, board, rules, prefer_y_long)
    # KPI
    alloc_time = next((e["sec"] for e in errors if e.get("code")=="INFO-TIME" and e.get("phase")=="allocation"), 0.0)
    st.session_state.results = {
        "panels": panels,
        "errors": errors,
        "placements": placements,
        "utilization": util,
        "num_sheets": num_sheets,
        "alloc_time": alloc_time
    }
    st.success(get_text("execution_success", current_lang).format(pitch=stud_pitch, board=selected_board))

# ===== 1) 案件ビュー =====
with tab1:
    st.subheader(get_text("project_info", current_lang))
    c1, c2 = st.columns([1,1])
    with c1:
        st.write(f"**{get_text('project_id', current_lang)}**: {project.project_id}")
        st.write(f"**{get_text('project_name', current_lang)}**: {project.name}")
        st.write(f"**{get_text('room', current_lang)}**: {project.room.room_id} / {get_text('use_type', current_lang)}={project.room.use_type}, {get_text('floor', current_lang)}={project.room.floor}")
        st.write(f"**{get_text('wall_height', current_lang)}**: {project.room.height} mm")
    with c2:
        st.write(f"**{get_text('opening_list', current_lang)}**")
        df_op = pd.DataFrame([{
            "opening_id": op.opening_id,
            "wall": op.wall,
            "type": op.type,
            "width": op.width,
            "height": op.height,
            "sill_height": op.sill_height,
            "offset": op.offset_from_wall_start
        } for op in project.openings])
        st.dataframe(df_op, use_container_width=True, height=180)
        
        st.write(f"**{get_text('wall_info', current_lang)}**")
        if st.session_state.results:
            wall_info = calculate_corner_winning_rules(project.room.polygon, project.room.wall_thickness)
            df_wall = pd.DataFrame([{
                "wall_id": wid,
                "length": f"{wall['length']:.0f}mm",
                "base_length": f"{wall['base_length']:.0f}mm",
                "direction": wall['direction']
            } for wid, wall in wall_info.items()])
            st.dataframe(df_wall, use_container_width=True, height=180)

    st.divider()
    st.subheader(get_text("kpi_summary", current_lang))
    res = st.session_state.results
    util = res.get("utilization", 0.0)
    sheets = res.get("num_sheets", 0)
    errors = res.get("errors", [])
    err_count = len([e for e in errors if str(e.get("code","")).startswith("E-")])

    c1, c2, c3 = st.columns(3)
    c1.metric(get_text("yield_rate", current_lang), f"{util*100:.1f}%")
    c2.metric(get_text("sheet_count", current_lang), f"{sheets}")
    c3.metric(get_text("error_count", current_lang), f"{err_count}")

    st.divider()
    st.subheader(get_text("plan_preview", current_lang))
    # Plotlyを使用した平面プレビュー
    fig_plan = create_room_plan_plotly(project)
    st.plotly_chart(fig_plan, use_container_width=True)
    
    st.subheader(get_text("3d_elevation", current_lang))
    # 3D表示（パネル情報が必要なので、結果がある場合のみ表示）
    panels = st.session_state.results.get("panels", [])
    if panels:
        fig_3d = create_3d_elevation_view(project, panels)
        st.plotly_chart(fig_3d, use_container_width=True)
    else:
        st.info(get_text("3d_info", current_lang))

# ===== 2) 割付ビュー =====
with tab2:
    st.subheader(get_text("wall_elevation", current_lang))
    panels = st.session_state.results.get("panels", [])
    
    # 出隅ルールを適用した壁情報を取得
    wall_info = calculate_corner_winning_rules(project.room.polygon, project.room.wall_thickness)
    H = project.room.height

    for wid in ["W1","W2","W3","W4"]:
        ops = [op for op in project.openings if op.wall == wid]
        wall_length = wall_info[wid]["length"]
        # Plotlyを使用した壁立面図（出隅ルール適用後の実際の長さを使用）
        fig_wall = create_wall_elevation_plotly(wid, wall_length, H, panels, ops)
        st.plotly_chart(fig_wall, use_container_width=True)

    st.info(get_text("color_info", current_lang))
    st.info(get_text("constraint_info", current_lang))
    
    # 間柱ピッチ設定
    st.subheader(get_text("stud_setting", current_lang))
    stud_pitch_new = st.selectbox(get_text("stud_pitch", current_lang), [455.0, 303.0], index=0, format_func=lambda x: f"{x:.0f}mm", key="stud_pitch_allocation")
    
    if st.button(get_text("recalculate", current_lang)):
        # 新しいピッチで再計算
        panels, errors = allocate_walls_with_architectural_constraints(project, board, rules, output_mode, stud_pitch_new)
        placements, util, num_sheets = simple_nesting(panels, board, rules, False)
        st.session_state.results = {
            "panels": panels,
            "errors": errors,
            "placements": placements,
            "utilization": util,
            "num_sheets": num_sheets,
            "alloc_time": 0.0
        }
        st.success(f"{get_text('stud_pitch', current_lang)} {stud_pitch_new:.0f}mm {get_text('recalculated', current_lang)}")
        # 再計算結果を即時反映
        st.rerun()

    # 自動修正（試作）
    if st.button(get_text("auto_fix", current_lang)):
        fixed = []
        for p in panels:
            if p.w < rules.min_piece:
                # 簡易処理：最小片違反は「備考」追記のみ（本PoCでは幅調整なし）
                p.note = (p.note or "") + " / 最小片違反"
            fixed.append(p)
        st.session_state.results["panels"] = fixed
        st.success(get_text("auto_fixed", current_lang))

# ===== 3) 板取ビュー =====
with tab3:
    st.subheader(get_text("nesting_preview", current_lang))
    placements = st.session_state.results.get("placements", [])
    util = st.session_state.results.get("utilization", 0.0)
    
    if placements:
        fig_nesting = create_nesting_plotly(placements, board)
        if fig_nesting:
            st.plotly_chart(fig_nesting, use_container_width=True)
        st.success(f"{get_text('utilization_rate', current_lang)}: {util*100:.1f}%")
    else:
        st.info(get_text("nesting_info", current_lang))

# ===== 4) 図面・帳票ビュー =====
with tab4:
    st.subheader(get_text("table_output", current_lang))
    panels = st.session_state.results.get("panels", [])
    errors = st.session_state.results.get("errors", [])
    placements = st.session_state.results.get("placements", [])
    df_p = df_panels(panels)
    df_e = df_errors(errors)
    df_s = df_boards(placements, board)

    st.write(f"**{get_text('parts_table', current_lang)}**")
    st.dataframe(df_p, use_container_width=True)
    # NOTE: Windows Excel での文字化け対策として UTF-8 BOM 付きを使用
    st.download_button(get_text("download_parts", current_lang), data=df_p.to_csv(index=False).encode("utf-8-sig"), file_name="panels.csv", mime="text/csv")

    st.write(f"**{get_text('sheet_layout', current_lang)}**")
    st.dataframe(df_s, use_container_width=True, height=200)
    # NOTE: Windows Excel での文字化け対策として UTF-8 BOM 付きを使用
    st.download_button(get_text("download_nesting", current_lang), data=df_s.to_csv(index=False).encode("utf-8-sig"), file_name="nesting.csv", mime="text/csv")

    st.write(f"**{get_text('error_list', current_lang)}**")
    st.dataframe(df_e, use_container_width=True, height=160)
    # NOTE: Windows Excel での文字化け対策として UTF-8 BOM 付きを使用
    st.download_button(get_text("download_errors", current_lang), data=df_e.to_csv(index=False).encode("utf-8-sig"), file_name="errors.csv", mime="text/csv")

# ===== 5) マスター内容 =====
with tab5:
    st.subheader(get_text("current_master", current_lang))
    st.json({
        "board": asdict(board),
        "rules": asdict(rules),
        "output_mode": output_mode
    })

st.caption(get_text("footer_note1", current_lang))
st.caption(get_text("footer_note2", current_lang))