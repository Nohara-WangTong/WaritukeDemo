# 割付・板取 PoC — システム説明書

## 1. 概要

本システムは、**石膏ボードの壁面への割付（パネル配置）** と **原板からの板取（ネスティング）** を一貫して行う **Proof of Concept（PoC）** の Web アプリケーションです。

- **対象**: 四角形の部屋を前提とし、扉・窓などの開口部を持つ 1 部屋
- **入力**: デモ案件（初期表示）または **CEDXM**（Construction Exchange Data XML）形式のファイル
- **出力**: 壁ごとの割付結果、原板への板取結果、部材表・エラー一覧の CSV ダウンロード
- **UI**: 多言語対応（日本語・英語・中国語・ベトナム語）、6 タブ構成のメイン画面とサイドバー

建築的な制約（間柱ピッチ 455mm/303mm、出隅の勝ち負けルール、開口部のクリッピング）を考慮した割付と、棚（Shelf）法による簡易板取を実装しています。

---

## 2. 主な機能一覧

| カテゴリ | 機能 | 説明 |
|----------|------|------|
| **入力** | デモ案件 | 起動時にサンプル部屋（7200×5400mm、扉1・窓2）を自動読み込み |
| **入力** | CEDXM 読み込み | XML 形式で部屋・開口を定義したファイルをアップロードして案件に反映 |
| **入力** | 壁高さによる板サイズ自動選択 | 2420mm 以下→3×8、2730mm 以下→3×9、それ以上→3×10 |
| **割付** | 建築的制約に基づく割付 | 間柱グリッド・出隅勝ち負け・開口クリッピングを適用 |
| **割付** | 外周壁＋新規壁 | W1～W4 に加え、平面図エディタで作成した内壁（W5,W6,…）も割付対象 |
| **板取** | 棚（Shelf）法板取 | 歩留り優先／長手優先のヒューリスティクスで原板に配置 |
| **表示** | 平面図・3D 見付図 | Plotly によるインタラクティブな 2D/3D 表示 |
| **表示** | 壁立面・割付プレビュー | 壁ごとの間柱・パネル・開口を色分けして表示 |
| **編集** | 壁編集モード | マウスで「壁を描く」「部屋を描く」により新規壁を追加し、割付・板取に反映 |
| **出力** | 部材表・板取結果・エラー CSV | UTF-8 BOM 付き CSV でダウンロード（Excel での文字化け対策済み） |
| **設定** | 多言語 UI | 日本語・English・中文・Tiếng Việt の切り替え |
| **設定** | 板サイズ・規格・板取ルール | 6. 設定タブで詳細パラメータを変更可能 |

---

## 3. システムの処理フロー

```
[入力]
  ├ デモ案件 (load_demo_project)  … 初期表示
  └ CEDXM ファイル (load_cedxm)   … 部屋・開口を XML から生成
           ↓
  Project（案件ID・部屋・開口一覧）
  BoardMaster（板サイズ: 壁高さから自動 or 手動選択）
  Rules（最小片・クリアランス・刃厚・ジョイント）
           ↓
[実行ボタン押下]
           ↓
  1) 構造要素生成 (structural)
     ・通り芯・柱・梁・間柱（キングスタッド含む）を stud_pitch（455/303mm）で生成
           ↓
  2) 割付 (allocating)
     ・出隅勝ち負けルールで壁長さを調整（calculate_corner_winning_rules）
     ・間柱グリッド生成（generate_stud_grid）
     ・開口部でパネルをクリップ（clip_panel_by_openings）
     ・allocate_walls_with_architectural_constraints で全壁（外周＋extra_walls）を処理
           ↓
  panels（壁別・座標・寸法・真物/端材等）、errors（情報・警告・エラー）
           ↓
  3) 板取 (nesting)
     ・simple_nesting（棚法）で panels を原板に配置
     ・回転許可時は歩留り優先、長手優先は設定で切り替え
           ↓
  placements（シート番号・x,y,w,h・回転）、utilization、num_sheets
           ↓
[表示・出力]
  ・案件ビュー：平面図・3D 見付図・KPI
  ・割付ビュー：壁立面・間柱ピッチ再計算・最小片自動修正（備考付与）
  ・板取ビュー：原板レイアウト・利用率
  ・図面・帳票：部材表・板取CSV・エラーCSV ダウンロード
```

---

## 4. 画面構成

### 4.1 全体レイアウト

- **上部**: タイトル「割付・板取 PoC」、キャプション（対象・多言語・PoC 最小実装の注記）
- **左サイドバー**: 言語選択、CEDXM 読み込み、板サイズ選択、**▶ 割付・板取を実行** ボタン
- **中央**: 6 つのタブ（1. 案件ビュー ～ 6. 設定）
- **下部**: フッター（PoC の範囲・CAD エンジンについての注記）

### 4.2 タブ別の内容

| タブ | 内容 |
|------|------|
| **1. 案件ビュー** | 案件情報（ID・部屋・開口一覧・壁情報）／KPI（歩留まり・ボード枚数・エラー数）／平面図（Plotly）／壁編集モード（壁・部屋を描いて新規壁追加）／3D 見付図 |
| **2. 割付ビュー** | 壁ごとのタブ（W1～W4＋新規壁 W5…）で立面・割付プレビュー／色凡例・建築的制約の説明／間柱ピッチ変更と再計算／最小片の一括自動修正（備考フラグ付与） |
| **3. 板取ビュー** | 原板への配置図（Plotly）／推定利用率（総合） |
| **4. 図面・帳票ビュー** | 部材表（割付）・ボード配置（板取）・エラー一覧のデータフレーム表示と CSV ダウンロード |
| **5. マスター内容** | 現在の board・rules・output_mode を JSON 表示 |
| **6. 設定** | 板サイズ・回転許可・出力形態／規格・ルール（最小片・クリアランス・刃厚・ジョイント）／板取ヒューリスティクス（歩留り優先／長手優先） |

---

## 5. 入力データ仕様

### 5.1 デモ案件（初期表示）

- **部屋**: R001、1 階、居室、多角形 7200×5400mm、高さ 2400mm、壁厚 100mm
- **開口**: 扉 1（W1）、窓 2（W3）
- 起動時に `load_demo_project()` で読み込まれ、`st.session_state.project` に保持されます。

### 5.2 CEDXM（Construction Exchange Data XML）

外部ツールや手編集で作成した XML で、部屋と開口を定義します。

- **ルート**: `CEDXM` または `Project`
- **Project**: 属性 `id`, `name`
- **Room**: 属性 `id`, `floor`, `use_type`, `height`, `wall_thickness`
- **Polygon**: 子要素 `Point` で `x`, `y`（mm）を列挙（時計回り推奨、4 点で四角形）
- **Openings**: 子要素 `Opening`。属性 `id`, `wall`(W1～W4), `type`(door/window), `width`, `height`, `sill_height`, `offset`(数値 mm または "center")

例（`sample1.cedxm` の要約）:

```xml
<CEDXM version="1.0">
  <Project id="SAMPLE-001" name="サンプル案件（壁高さ2730mm）">
    <Room id="R001" floor="1" use_type="居室" height="2730" wall_thickness="100">
      <Polygon>
        <Point x="0" y="0"/>
        <Point x="3600" y="0"/>
        <Point x="3600" y="2700"/>
        <Point x="0" y="2700"/>
      </Polygon>
      <Openings>
        <Opening id="O-D1" wall="W1" type="door" width="800" height="2000" sill_height="0" offset="600"/>
        <Opening id="O-W1" wall="W3" type="window" width="1200" height="1000" sill_height="900" offset="center"/>
      </Openings>
    </Room>
  </Project>
</CEDXM>
```

CEDXM 読み込み後、壁高さに応じて石膏ボードが自動選択され、案件がセッションに設定されます。

---

## 6. 建築的制約と割付ルール

- **間柱グリッド**: 壁長さ方向に 455mm または 303mm ピッチで間柱位置を生成。割付はこのグリッドに沿って行われます。
- **出隅の勝ち負けルール**: 時計回りで W1→W2→W3→W4→W1 の順で「勝ち」側を通し、「負け」側は壁厚分短くします。これにより、角で二重にカウントされない実務に近い壁長さになります。
- **開口部のクリッピング**: 扉・窓の範囲はパネル配置から除外し、開口として表示（暗赤色）します。
- **新規壁（W5 以降）**: 平面図エディタで追加した壁は片側面のみ割付対象です。内壁で両面施工する場合は、同一壁を 2 回割付する運用で対応します。

---

## 7. 板取（ネスティング）ロジック

- **アルゴリズム**: 棚（Shelf）法。パネルを面積の大きい順に並べ、原板（910×2430 等）上に順次配置します。
- **回転**: `board.rotatable` が True のとき、必要に応じて 90° 回転して配置可能。原板を超える寸法のパネルは回転で収まる場合のみ取り込みます。
- **ヒューリスティクス**: 「歩留り優先」（機械加工想定）では回転を活かし、「長手優先」（手加工想定）では回転を制限するオプションを設定タブで選択できます。
- **出力**: 各配置は `NestPlacement`（sheet_id, x, y, w, h, rotated, panel_ref）で、板取ビューと CSV に反映されます。

---

## 8. モジュール構成

```
app.py                     # エントリポイント（セッション初期化・タブ・実行トリガー・フッター）
src/
├── i18n.py                # 多言語辞書（LANGUAGES, TRANSLATIONS）と get_text()
├── masterdata.py          # データクラス: BoardMaster, Rules, Room, Opening, Project, Panel, StudGrid, NestPlacement
├── input.py               # load_demo_project() … デモ案件の生成
├── cedxm.py               # load_cedxm(), create_board_from_height() … CEDXM 解析と壁高さによる板選択
├── logic.py               # room_wall_lengths(), place_opening_position() … 壁長・開口オフセット
├── allocating.py          # 割付: 勝ち負けルール・間柱グリッド・開口クリップ・allocate_walls_*
├── nesting.py             # simple_nesting() … 棚法板取
├── structural.py          # 構造要素: Column, Beam, Stud, GridLine, StructuralSystem, generate_structural_system()
├── visualization.py       # Plotly: 平面図・3D 見付図・壁立面・板取図
├── structural_viz.py      # 構造要素の可視化支援
├── output.py              # df_panels(), df_errors(), df_boards(), fig_to_png_bytes()
├── interactive_plan.py    # 平面図エディタ: 壁を描く・部屋を描く（create_interactive_plan_editor）
├── wall_editor.py         # WallSegment, スナップ・壁/部屋作成（create_wall_from_line, create_walls_from_area）
├── legacy_viz.py          # 互換用 matplotlib 可視化（plot_room_and_openings, plot_wall_elevation, plot_nesting）
└── ui/
    ├── sidebar.py         # 言語・CEDXM・板サイズ・実行ボタン
    ├── tab_project.py     # 1. 案件ビュー
    ├── tab_allocation.py   # 2. 割付ビュー
    ├── tab_nesting.py     # 3. 板取ビュー
    ├── tab_drawings.py    # 4. 図面・帳票ビュー
    ├── tab_master.py      # 5. マスター内容
    └── tab_settings.py    # 6. 設定
```

---

## 9. 起動方法・必要環境

### 9.1 必要環境

- Python 3.10 以上を推奨
- 依存パッケージ: `requirements.txt` に記載
  - streamlit
  - plotly
  - pandas
  - numpy
  - matplotlib

### 9.2 インストールと起動

```bash
# リポジトリルートで
pip install -r requirements.txt
streamlit run app.py
```

ブラウザで `http://localhost:8501` が開きます。  
デプロイ環境では、例: `https://xxxx.streamlit.app/` で公開する形になります。

### 9.3 バッチ起動（Windows）

`0-run_app.bat` を実行すると、上記と同様に Streamlit が起動します。

---

## 10. 用語・略称

| 用語 | 説明 |
|------|------|
| **割付** | 壁面上に石膏ボードパネルをどの位置・寸法で配置するかの決定 |
| **板取（ネスティング）** | 割付で得られたパネルを、原板（910×2430mm 等）からどのように切り出すかの配置 |
| **CEDXM** | Construction Exchange Data XML。部屋・開口などを交換するための XML 形式 |
| **間柱ピッチ** | 間柱の間隔（455mm / 303mm）。割付のグリッド基準 |
| **出隅の勝ち負け** | 角で接する 2 壁のうち、どちらを「通し」にしてどちらを短くするかのルール |
| **歩留まり** | 板取で有効に使えた面積の割合（利用率） |

---

## 11. 制限事項・今後の拡張（PoC の範囲）

- **部屋形状**: 四角形（多角形 4 点）を前提。L 字型などは未対応です。
- **板形状**: 矩形のみ。切欠き・角落としは将来拡張予定です。
- **編集**: 壁の追加は平面図エディタで可能。undo/redo・スナップの高度な CAD 機能は未実装です。
- **出力**: CSV と画面上の図が中心。PDF/DXF 出力は開発プランに含まれます。

詳細な機能比較・開発プランは `3-機能比較・開発プラン.txt`、操作手順は `2-操作手順書.txt` を参照してください。
