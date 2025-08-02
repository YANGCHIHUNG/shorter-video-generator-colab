#!/usr/bin/env python3
"""
測試修復後的字幕生成器
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "utility"))

def test_subtitle_generator():
    """測試字幕生成器的基本功能"""
    print("🧪 測試字幕生成器基本功能...")
    
    try:
        from utility.improved_hybrid_subtitle_generator import ImprovedHybridSubtitleGenerator
        
        # 創建字幕生成器
        generator = ImprovedHybridSubtitleGenerator(
            model_size="small",
            traditional_chinese=True,
            subtitle_length_mode="auto",
            chars_per_line=15,
            max_lines=2
        )
        
        print("✅ 字幕生成器初始化成功")
        
        # 測試 SRT 內容生成
        test_segments = [
            {"start": 0.0, "end": 3.0, "text": "這是第一段測試字幕"},
            {"start": 3.0, "end": 6.0, "text": "這是第二段測試字幕"},
            {"start": 6.0, "end": 9.0, "text": "這是第三段測試字幕"}
        ]
        
        srt_content = generator._generate_srt_content(test_segments)
        print("✅ SRT 內容生成成功")
        print("📋 生成的 SRT 內容:")
        print(srt_content)
        
        # 測試字幕切分
        long_text = "這是一段很長的測試文字，需要被切分成多行來避免超出螢幕顯示範圍"
        split_result = generator._split_long_subtitle(long_text, 0.0, 5.0)
        print(f"✅ 長字幕切分成功，切分為 {len(split_result)} 段")
        for i, segment in enumerate(split_result):
            print(f"  段落 {i+1}: {segment['text']}")
        
        print("✅ 所有基本功能測試通過！")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_subtitle_generator()
