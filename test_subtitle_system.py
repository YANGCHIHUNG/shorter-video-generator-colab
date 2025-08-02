#!/usr/bin/env python3
"""
測試簡化後的字幕生成系統 - 純用戶輸入文字
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "utility"))

from utility.improved_hybrid_subtitle_generator import ImprovedHybridSubtitleGenerator

def test_simplified_subtitle_generation():
    """測試簡化的字幕生成功能"""
    print("🎬 測試簡化字幕生成系統...")
    
    # 創建測試用戶輸入文字
    user_text = """
    大家好，歡迎來到我們的頻道。
    今天我們要討論人工智慧的發展。
    機器學習已經改變了我們的生活。
    未來還會有更多的驚喜等待我們。
    """
    
    try:
        # 創建字幕生成器（使用新的簡化參數）
        generator = ImprovedHybridSubtitleGenerator(
            model_size="small",
            traditional_chinese=True,
            subtitle_length_mode="auto",
            chars_per_line=15,
            max_lines=2
        )
        
        print("✅ 字幕生成器初始化成功")
        
        # 測試虛擬音頻文件
        test_audio_path = project_root / "test_data" / "test_audio.wav"
        
        # 如果沒有實際音頻文件，創建一個虛擬的測試
        if not test_audio_path.exists():
            print("⚠️  沒有找到測試音頻文件，使用模擬測試...")
            
            # 模擬 Whisper 轉錄結果
            mock_segments = [
                {"start": 0.0, "end": 3.0, "text": "大家好，歡迎來到我們的頻道"},
                {"start": 3.0, "end": 6.0, "text": "今天我們要討論人工智慧的發展"},
                {"start": 6.0, "end": 9.0, "text": "機器學習已經改變了我們的生活"},
                {"start": 9.0, "end": 12.0, "text": "未來還會有更多的驚喜等待我們"}
            ]
            
            # 直接測試文字映射功能
            mapped_segments = generator._simple_map_user_text_to_timeline(mock_segments, user_text)
            
            print(f"📝 映射結果：")
            for i, segment in enumerate(mapped_segments):
                print(f"  段落 {i+1}: {segment['start']:.1f}s - {segment['end']:.1f}s")
                print(f"           原始: {segment.get('original_text', 'N/A')}")
                print(f"           用戶: {segment['text']}")
                print()
            
            # 生成 SRT 字幕
            srt_content = generator._generate_srt_from_segments(mapped_segments)
            print("📋 生成的 SRT 字幕：")
            print(srt_content)
            
        else:
            print(f"🎵 找到音頻文件: {test_audio_path}")
            # 使用實際音頻文件進行測試
            with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as srt_file:
                srt_path = srt_file.name
            
            result = generator.generate_hybrid_subtitles(
                audio_path=str(test_audio_path),
                user_text=user_text,
                output_srt_path=srt_path
            )
            
            if os.path.exists(srt_path):
                with open(srt_path, 'r', encoding='utf-8') as f:
                    srt_content = f.read()
                print("✅ SRT 字幕生成成功：")
                print(srt_content)
                os.unlink(srt_path)  # 清理測試文件
            else:
                print("❌ SRT 字幕文件未生成")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

def test_font_detection():
    """測試字體偵測功能"""
    print("\n🔍 測試字體偵測功能...")
    
    try:
        from utility.improved_hybrid_subtitle_generator import get_available_chinese_font
        
        font_path = get_available_chinese_font()
        if font_path:
            print(f"✅ 找到中文字體: {font_path}")
        else:
            print("⚠️  未找到中文字體，將使用系統默認字體")
            
    except Exception as e:
        print(f"❌ 字體偵測失敗: {e}")

if __name__ == "__main__":
    print("🧪 開始測試簡化字幕系統...\n")
    
    test_font_detection()
    test_simplified_subtitle_generation()
    
    print("\n✨ 測試完成！")
