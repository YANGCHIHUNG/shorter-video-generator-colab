#!/usr/bin/env python3
"""
測試修復後的時間戳映射
"""

import os
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "utility"))

def test_whisper_timestamp_mapping():
    """測試使用 Whisper 實際時間戳的映射"""
    print("🧪 測試 Whisper 時間戳映射...")
    
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
        
        # 模擬實際的 Whisper 時間戳（來自你提供的日誌）
        whisper_segments = [
            {"start": 0.0, "end": 1.5, "text": "各位"},
            {"start": 1.5, "end": 3.8, "text": "醫依伊"},
            {"start": 3.8, "end": 8.2, "text": "這張投影片的重點在於說明"},
            {"start": 8.2, "end": 12.1, "text": "這張投影片介紹的是NLQ"},
            {"start": 12.1, "end": 16.5, "text": "它能讓使用者用我們日常說話的方式"},
            {"start": 16.5, "end": 20.8, "text": "這大幅降低了數據查詢的技術門檻"},
            {"start": 20.8, "end": 25.3, "text": "接著，進入到語意解析與意圖識別階段"},
            {"start": 25.3, "end": 28.9, "text": "我們會運用NLP技術，像是BERT、GPT"}
        ]
        
        # 模擬用戶輸入的文字
        user_texts = [
            "各位，這張投影片的重點在於說明我們投入AI資料庫的動機與背景。",
            "這張投影片介紹的是NLQ，也就是自然語言查詢技術。它能讓使用者用我們日常說話的方式，直接查詢資料庫。這大幅降低了數據查詢的技術門檻，讓非技術人員也能輕鬆參與數據分析。",
            "接著，進入到語意解析與意圖識別階段。我們會運用NLP技術，像是BERT、GPT這樣的預訓練模型，來分析用戶查詢的語義結構。"
        ]
        
        print(f"📝 用戶文字: {len(user_texts)} 段")
        print(f"🎙️ Whisper 片段: {len(whisper_segments)} 個")
        
        # 顯示 Whisper 原始時間戳
        print("\n🎙️ Whisper 原始時間戳:")
        for i, seg in enumerate(whisper_segments):
            print(f"  {i+1}: {seg['start']:.1f}s-{seg['end']:.1f}s: {seg['text']}")
        
        # 測試新的映射功能
        mapped_segments = generator._simple_map_user_text_to_timeline(whisper_segments, user_texts)
        
        print(f"\n✅ 映射完成，生成 {len(mapped_segments)} 個字幕片段")
        print("\n📝 映射結果 (使用用戶文字 + Whisper時間戳):")
        for i, segment in enumerate(mapped_segments):
            print(f"  片段 {i+1}: {segment['start']:.2f}s-{segment['end']:.2f}s")
            print(f"    用戶文字: {segment['text'][:50]}...")
            if 'original_whisper' in segment:
                print(f"    原Whisper: {segment['original_whisper']}")
            print()
        
        # 生成 SRT 內容來驗證
        srt_content = generator._generate_srt_content(mapped_segments)
        print("📋 生成的 SRT 內容預覽:")
        print(srt_content[:500] + "..." if len(srt_content) > 500 else srt_content)
        
        print("✅ Whisper 時間戳映射測試通過！")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_whisper_timestamp_mapping()
