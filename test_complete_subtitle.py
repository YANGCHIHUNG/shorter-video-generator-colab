#!/usr/bin/env python3
"""
測試完整的字幕生成流程
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "utility"))

def test_complete_subtitle_flow():
    """測試完整的字幕生成流程"""
    print("🧪 測試完整字幕生成流程...")
    
    try:
        from utility.improved_hybrid_subtitle_generator import ImprovedHybridSubtitleGenerator
        
        # 創建字幕生成器（使用與實際API相同的參數）
        generator = ImprovedHybridSubtitleGenerator(
            model_size="small",
            traditional_chinese=True,
            subtitle_length_mode="auto",
            chars_per_line=15,
            max_lines=2
        )
        
        print("✅ 字幕生成器初始化成功")
        
        # 模擬用戶輸入的文字（來自實際錯誤日誌的內容）
        user_texts = [
            "大家好郝好郝，今天我們要談談為什麼我們投入這個專案。",
            "首先，從大方向來看，AI市場正以驚人的速度成長。",
            "各位，今天要跟大家介紹的是NLQ，也就是自然語言查詢。"
        ]
        
        # 模擬 Whisper 轉錄結果（來自實際錯誤日誌）
        whisper_segments = [
            {"start": 0.0, "end": 3.71, "text": "大家好，今天我們要談談為什麼"},
            {"start": 3.71, "end": 7.42, "text": "首先，從大方向來看"},
            {"start": 7.42, "end": 11.13, "text": "各位，今天要跟大家介紹"},
            {"start": 11.13, "end": 15.37, "text": "簡單來說，它讓使用者可以"},
            {"start": 15.37, "end": 19.09, "text": "好的"},
            {"start": 19.09, "end": 22.80, "text": "針對這張關於流程的投影片"},
            {"start": 22.80, "end": 25.98, "text": "我的講稿會這樣說"}
        ]
        
        print(f"📝 用戶文字: {len(user_texts)} 段")
        print(f"🎙️ Whisper 片段: {len(whisper_segments)} 個")
        
        # 測試簡化映射功能
        mapped_segments = generator._simple_map_user_text_to_timeline(whisper_segments, user_texts)
        print(f"✅ 映射完成，生成 {len(mapped_segments)} 個字幕片段")
        
        # 顯示映射結果
        for i, segment in enumerate(mapped_segments):
            print(f"  片段 {i+1}: {segment['start']:.2f}s-{segment['end']:.2f}s: {segment['text'][:20]}...")
        
        # 生成 SRT 內容
        srt_content = generator._generate_srt_content(mapped_segments)
        print("✅ SRT 內容生成成功")
        
        # 保存測試 SRT 文件
        test_srt_path = project_root / "test_output.srt"
        with open(test_srt_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        print(f"💾 測試 SRT 文件已保存: {test_srt_path}")
        print("📋 SRT 內容預覽:")
        print(srt_content[:300] + "..." if len(srt_content) > 300 else srt_content)
        
        # 清理測試文件
        if test_srt_path.exists():
            test_srt_path.unlink()
            print("🗑️ 測試文件已清理")
        
        print("✅ 完整字幕生成流程測試通過！")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complete_subtitle_flow()
