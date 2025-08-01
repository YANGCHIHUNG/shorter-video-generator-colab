#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試簡化的混合字幕生成器集成
"""

import sys
import os
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_simple_hybrid_integration():
    """測試簡化的混合字幕生成器集成"""
    try:
        # 測試導入
        logger.info("🧪 測試簡化混合字幕生成器導入...")
        from utility.simple_hybrid_subtitle_generator import SimpleHybridSubtitleGenerator
        
        logger.info("✅ 簡化混合字幕生成器導入成功")
        
        # 創建生成器實例
        logger.info("🏗️ 創建簡化混合字幕生成器...")
        generator = SimpleHybridSubtitleGenerator(
            model_size="tiny",  # 使用最小模型進行測試
            traditional_chinese=True
        )
        
        logger.info("✅ 簡化混合字幕生成器創建成功")
        
        # 測試時間格式化
        test_times = [0.0, 3.5, 67.123, 3661.789]
        logger.info("🕒 測試時間格式化功能...")
        for time_val in test_times:
            formatted = generator._format_time(time_val)
            logger.info(f"  {time_val}s -> {formatted}")
        
        # 測試文字映射
        logger.info("📝 測試文字映射功能...")
        
        # 模擬 Whisper 片段
        whisper_segments = [
            {"start": 0.0, "end": 5.0, "text": "模擬片段1"},
            {"start": 5.0, "end": 10.0, "text": "模擬片段2"},
            {"start": 10.0, "end": 15.0, "text": "模擬片段3"}
        ]
        
        # 用戶參考文字
        reference_texts = [
            "這是第一段用戶提供的正確文字內容。",
            "這是第二段用戶修正過的文字內容。",
            "這是第三段包含專業術語的文字內容。"
        ]
        
        # 執行映射
        mapped = generator._map_text_to_segments(whisper_segments, reference_texts)
        
        logger.info("📋 映射結果：")
        for i, segment in enumerate(mapped):
            logger.info(f"  片段 {i+1}: {segment['start']:.1f}s - {segment['end']:.1f}s")
            logger.info(f"    文字: {segment['text'][:30]}...")
        
        # 測試 SRT 生成
        logger.info("📄 測試 SRT 內容生成...")
        srt_content = generator._generate_srt_content(mapped)
        
        logger.info("📄 生成的 SRT 內容（前500字符）：")
        logger.info(srt_content[:500] + "..." if len(srt_content) > 500 else srt_content)
        
        # 測試中文轉換
        if generator.traditional_chinese and generator.zhconv:
            logger.info("🈶 測試中文繁簡轉換...")
            test_text = "机器学习和人工智能"
            converted = generator._convert_chinese(test_text)
            logger.info(f"  簡體: {test_text}")
            logger.info(f"  繁體: {converted}")
        
        logger.info("✅ 所有集成測試通過！")
        return True
        
    except ImportError as e:
        logger.error(f"❌ 導入錯誤: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_api_integration():
    """測試 API 集成"""
    try:
        logger.info("🔗 測試 API 集成...")
        
        # 測試 API 導入
        from api.whisper_LLM_api import SimpleHybridSubtitleGenerator as APISimpleHybrid
        
        if APISimpleHybrid is not None:
            logger.info("✅ API 中的簡化混合字幕生成器可用")
        else:
            logger.warning("⚠️ API 中的簡化混合字幕生成器不可用")
            return False
        
        # 測試基本創建
        generator = APISimpleHybrid(model_size="tiny", traditional_chinese=False)
        logger.info("✅ 通過 API 創建簡化混合字幕生成器成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ API 集成測試失敗: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 開始簡化混合字幕生成器集成測試...")
    
    success = True
    
    # 測試基本功能
    if not test_simple_hybrid_integration():
        success = False
    
    # 測試 API 集成
    if not test_api_integration():
        success = False
    
    if success:
        logger.info("🎉 所有集成測試通過！系統已準備好使用簡化的混合字幕功能。")
        logger.info("💡 主要功能：")
        logger.info("  - 使用 Whisper 獲取準確的時間戳")
        logger.info("  - 使用用戶文字作為字幕內容")
        logger.info("  - 支持繁體中文轉換")
        logger.info("  - 直接使用 FFmpeg 嵌入字幕")
    else:
        logger.error("💥 部分測試失敗，請檢查錯誤訊息。")
    
    sys.exit(0 if success else 1)
