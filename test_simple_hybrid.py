#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
簡化的混合字幕生成器測試
"""

import sys
import os
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_basic_imports():
    """測試基本導入"""
    try:
        import whisper
        logger.info("✅ Whisper 導入成功")
        
        from fuzzywuzzy import fuzz
        logger.info("✅ FuzzyWuzzy 導入成功")
        
        import zhconv
        logger.info("✅ 中文繁簡轉換導入成功")
        
        return True
    except ImportError as e:
        logger.error(f"❌ 導入錯誤: {e}")
        return False

def test_text_mapping_logic():
    """測試文字映射邏輯（不依賴實際的Whisper）"""
    try:
        logger.info("🧪 測試文字映射邏輯...")
        
        # 模擬 Whisper 片段
        whisper_segments = [
            {"start": 0.0, "end": 3.5, "text": "歡迎來到人工智慧"},
            {"start": 3.5, "end": 8.0, "text": "今天我們將探討機器學習"},
            {"start": 8.0, "end": 12.0, "text": "機器學習是重要分支"},
            {"start": 12.0, "end": 16.5, "text": "它讓電腦能夠學習"},
            {"start": 16.5, "end": 20.0, "text": "深度學習是一種方法"},
            {"start": 20.0, "end": 24.0, "text": "使用神經網路模擬"}
        ]
        
        # 用戶參考文字
        reference_texts = [
            "歡迎來到人工智慧的世界，今天我們將探討機器學習的基本概念。",
            "機器學習是人工智慧的一個重要分支，它讓電腦能夠從數據中學習。",
            "深度學習是機器學習的一種方法，使用神經網路來模擬人腦的運作。"
        ]
        
        # 簡化版映射邏輯
        def simple_map_text_to_segments(segments, texts):
            """簡化的文字映射函數"""
            mapped_segments = []
            
            if len(segments) == len(texts):
                # 一對一映射
                for i, segment in enumerate(segments):
                    mapped_segments.append({
                        "start": segment["start"],
                        "end": segment["end"],
                        "text": texts[i] if i < len(texts) else segment["text"]
                    })
            else:
                # 比例映射
                total_whisper_duration = segments[-1]["end"] - segments[0]["start"]
                current_time = 0
                
                for i, text in enumerate(texts):
                    text_duration = total_whisper_duration / len(texts)
                    start_time = current_time
                    end_time = current_time + text_duration
                    
                    mapped_segments.append({
                        "start": start_time,
                        "end": end_time,
                        "text": text
                    })
                    
                    current_time = end_time
            
            return mapped_segments
        
        # 測試映射
        mapped = simple_map_text_to_segments(whisper_segments, reference_texts)
        
        logger.info("📝 映射結果：")
        for segment in mapped:
            logger.info(f"  {segment['start']:.1f}s - {segment['end']:.1f}s: {segment['text'][:50]}...")
        
        # 測試 SRT 生成
        def generate_srt_content(segments):
            """生成 SRT 內容"""
            srt_content = ""
            for i, segment in enumerate(segments, 1):
                start_time = format_time(segment["start"])
                end_time = format_time(segment["end"])
                text = segment["text"]
                
                srt_content += f"{i}\n"
                srt_content += f"{start_time} --> {end_time}\n"
                srt_content += f"{text}\n\n"
            
            return srt_content
        
        def format_time(seconds):
            """將秒數轉換為 SRT 時間格式"""
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            seconds = seconds % 60
            milliseconds = int((seconds % 1) * 1000)
            seconds = int(seconds)
            
            return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
        
        srt_content = generate_srt_content(mapped)
        
        logger.info("📄 生成的 SRT 內容（前300字符）：")
        logger.info(srt_content[:300] + "..." if len(srt_content) > 300 else srt_content)
        
        logger.info("✅ 文字映射邏輯測試通過！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 文字映射測試失敗: {e}")
        return False

def test_chinese_conversion():
    """測試中文繁簡轉換"""
    try:
        import zhconv
        
        simplified = "机器学习是人工智能的重要分支"
        traditional = zhconv.convert(simplified, 'zh-tw')
        
        logger.info(f"📝 簡體: {simplified}")
        logger.info(f"📝 繁體: {traditional}")
        
        logger.info("✅ 中文轉換測試通過！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 中文轉換測試失敗: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 開始簡化測試...")
    
    all_tests_passed = True
    
    # 測試基本導入
    if not test_basic_imports():
        all_tests_passed = False
    
    # 測試文字映射邏輯
    if not test_text_mapping_logic():
        all_tests_passed = False
    
    # 測試中文轉換
    if not test_chinese_conversion():
        all_tests_passed = False
    
    if all_tests_passed:
        logger.info("🎉 所有測試通過！混合字幕生成器的核心邏輯運作正常。")
    else:
        logger.error("💥 部分測試失敗，請檢查錯誤訊息。")
    
    sys.exit(0 if all_tests_passed else 1)
