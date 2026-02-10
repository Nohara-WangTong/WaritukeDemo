"""
アプリケーションの基本的な動作確認テスト
"""
import sys

def test_imports():
    """必要なモジュールがインポートできるか確認"""
    try:
        import streamlit as st
        print("✓ Streamlit imported successfully")
        
        import plotly.graph_objects as go
        print("✓ Plotly imported successfully")
        
        from src.wall_editor import WallSegment, snap_to_grid, create_wall_from_line
        print("✓ wall_editor module imported successfully")
        
        from src.interactive_plan import create_interactive_plan_editor
        print("✓ interactive_plan module imported successfully")
        
        from src.masterdata import Project, Room
        print("✓ masterdata module imported successfully")
        
        from src.allocating import calculate_corner_winning_rules
        print("✓ allocating module imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def test_wall_editor_functions():
    """壁編集機能の基本的な動作確認"""
    try:
        from src.wall_editor import snap_to_grid, snap_to_horizontal_or_vertical
        
        # グリッドスナップのテスト
        result = snap_to_grid((1023, 2047))
        assert result == (1000, 2050), f"Expected (1000, 2050), got {result}"
        print("✓ snap_to_grid works correctly")
        
        # 水平・垂直スナップのテスト
        result = snap_to_horizontal_or_vertical((0, 0), (1000, 200))
        assert result == (1000, 0), f"Expected (1000, 0), got {result}"
        print("✓ snap_to_horizontal_or_vertical works correctly")
        
        return True
    except Exception as e:
        print(f"✗ Function test error: {e}")
        return False

def main():
    print("=" * 50)
    print("アプリケーション動作確認テスト")
    print("=" * 50)
    print()
    
    # インポートテスト
    print("1. モジュールインポートテスト")
    print("-" * 50)
    import_ok = test_imports()
    print()
    
    # 機能テスト
    print("2. 壁編集機能テスト")
    print("-" * 50)
    function_ok = test_wall_editor_functions()
    print()
    
    # 結果
    print("=" * 50)
    if import_ok and function_ok:
        print("✓ すべてのテストが成功しました！")
        print("アプリケーションを起動できます: streamlit run app.py")
        return 0
    else:
        print("✗ テストに失敗しました")
        return 1

if __name__ == "__main__":
    sys.exit(main())
