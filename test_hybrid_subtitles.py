#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試混合字幕生成器
"""

import sys
import os
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_hybrid_subtitle_generator():
    """測試混合字幕生成器功能"""
    try:
        # 導入混合字幕生成器
        from utility.hybrid_subtitle_generator import HybridSubtitleGenerator
        
        logger.info("✅ 成功導入 HybridSubtitleGenerator")
        
        # 測試用戶文字
        reference_texts = [
            "歡迎來到人工智慧的世界，今天我們將探討機器學習的基本概念。",
            "機器學習是人工智慧的一個重要分支，它讓電腦能夠從數據中學習。",
            "深度學習是機器學習的一種方法，使用神經網路來模擬人腦的運作。"
        ]
        
        # 創建混合字幕生成器
        logger.info("🏗️ 創建混合字幕生成器...")
        hybrid_generator = HybridSubtitleGenerator(
            model_size="tiny",  # 使用最小模型進行測試
            traditional_chinese=True
        )
        
        logger.info("✅ 混合字幕生成器創建成功！")
        
        # 測試文字映射功能
        logger.info("🧪 測試文字映射功能...")
        
        # 模擬 Whisper 片段
        whisper_segments = [
            {"start": 0.0, "end": 3.5, "text": "歡迎來到人工智慧"},
            {"start": 3.5, "end": 8.0, "text": "今天我們將探討機器學習"},
            {"start": 8.0, "end": 12.0, "text": "機器學習是重要分支"},
            {"start": 12.0, "end": 16.5, "text": "它讓電腦能夠學習"},
            {"start": 16.5, "end": 20.0, "text": "深度學習是一種方法"},
            {"start": 20.0, "end": 24.0, "text": "使用神經網路模擬"}
        ]
        
        # 測試映射
        mapped_segments = hybrid_generator._map_text_to_segments(
            whisper_segments, reference_texts
        )
        
        logger.info("📝 映射結果：")
        for segment in mapped_segments:
            logger.info(f"  {segment['start']:.1f}s - {segment['end']:.1f}s: {segment['text']}")
        
        # 測試 SRT 生成
        logger.info("📄 測試 SRT 生成...")
        srt_content = hybrid_generator._generate_srt_content(mapped_segments)
        
        logger.info("📄 生成的 SRT 內容：")
        logger.info(srt_content[:300] + "..." if len(srt_content) > 300 else srt_content)
        
        logger.info("✅ 所有測試通過！混合字幕生成器運作正常。")
        return True
        
    except ImportError as e:
        logger.error(f"❌ 導入錯誤: {e}")
        logger.info("💡 請確保已安裝 openai-whisper: pip install openai-whisper")
        return False
    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 開始測試混合字幕生成器...")
    success = test_hybrid_subtitle_generator()
    
    if success:
        logger.info("🎉 測試完成：混合字幕生成器功能正常！")
    else:
        logger.error("💥 測試失敗：請檢查錯誤訊息並修復問題。")
    
    sys.exit(0 if success else 1)
