#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試語速計算字幕生成器
"""

import os
import sys
import logging

# 設置路徑
sys.path.append(os.path.dirname(__file__))

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_speech_rate_generator():
    """測試語速計算字幕生成器"""
    try:
        from utility.improved_hybrid_subtitle_generator import SpeechRateSubtitleGenerator
        
        # 創建生成器實例
        generator = SpeechRateSubtitleGenerator(
            traditional_chinese=False,
            chars_per_line=25
        )
        
        logger.info("✅ SpeechRateSubtitleGenerator 創建成功")
        
        # 測試文本切分功能
        test_text = "這是第一句話。這是第二句話！這是第三句話？還有第四句。"
        sentences = generator._split_sentences_by_punctuation(test_text)
        
        logger.info(f"📝 文本切分測試:")
        logger.info(f"  原文: {test_text}")
        logger.info(f"  切分結果: {len(sentences)} 個句子")
        for i, sentence in enumerate(sentences):
            logger.info(f"    句子 {i+1}: {sentence}")
        
        # 測試中文轉換功能
        if generator.zhconv:
            converted = generator._convert_chinese("简体中文测试")
            logger.info(f"🔄 中文轉換測試: 简体中文测试 → {converted}")
        
        # 測試字符計算功能
        effective_chars = generator._count_effective_characters("測試文字，包含標點！")
        logger.info(f"🔢 有效字符計算: 測試文字，包含標點！ → {effective_chars} 個字符")
        
        # 測試停頓時間計算
        pause_time = generator._calculate_pause_time("這是測試。包含停頓！")
        logger.info(f"⏱️ 停頓時間計算: {pause_time:.2f} 秒")
        
        # 測試語速計算
        speech_rate = generator._calculate_speech_rate("這是一個測試文本，用來計算語速。", 5.0)
        logger.info(f"📈 語速計算: {speech_rate:.2f} 字/秒")
        
        logger.info("✅ 所有測試通過!")
        return True
        
    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("🧪 開始測試語速計算字幕生成器...")
    success = test_speech_rate_generator()
    
    if success:
        logger.info("🎉 語速計算字幕生成器測試完成!")
    else:
        logger.error("💥 語速計算字幕生成器測試失敗!")
        sys.exit(1)
