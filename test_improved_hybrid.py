#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試改進的混合字幕生成器
"""

import sys
import os
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_improved_hybrid_subtitle_generator():
    """測試改進的混合字幕生成器"""
    try:
        # 測試導入
        logger.info("🧪 測試改進混合字幕生成器導入...")
        from utility.improved_hybrid_subtitle_generator import ImprovedHybridSubtitleGenerator
        
        logger.info("✅ 改進混合字幕生成器導入成功")
        
        # 創建生成器實例
        logger.info("🏗️ 創建改進混合字幕生成器...")
        generator = ImprovedHybridSubtitleGenerator(
            model_size="tiny",  # 使用最小模型進行測試
            traditional_chinese=True
        )
        
        logger.info("✅ 改進混合字幕生成器創建成功")
        
        # 測試文字分割功能
        logger.info("✂️ 測試文字分割功能...")
        test_texts = [
            "這是第一頁的內容。它包含了多個句子！也有問號的句子嗎？當然還有感嘆號！",
            "第二頁的內容比較簡短。只有兩個句子。",
            "第三頁內容更豐富，包含了各種標點符號。有逗號，有分號；也有冒號：內容很豐富！最後還有省略號..."
        ]
        
        for i, text in enumerate(test_texts):
            sentences = generator._split_text_into_sentences(text)
            logger.info(f"  頁面 {i+1} ({len(sentences)} 個句子):")
            for j, sentence in enumerate(sentences):
                logger.info(f"    句子 {j+1}: {sentence}")
        
        # 測試智能映射功能
        logger.info("🧠 測試智能映射功能...")
        
        # 模擬 Whisper 片段
        whisper_segments = [
            {"start": 0.0, "end": 5.2, "text": "这是第一段音频"},
            {"start": 5.2, "end": 8.7, "text": "第二段音频内容"},
            {"start": 8.7, "end": 12.1, "text": "第三段音频"},
            {"start": 12.1, "end": 16.5, "text": "第四段音频内容"},
            {"start": 16.5, "end": 20.0, "text": "最后一段音频"}
        ]
        
        # 測試不同映射策略
        logger.info("📋 測試一對一映射策略...")
        user_sentences = [
            "這是第一段正確的文字內容",
            "第二段用戶修正過的文字",
            "第三段包含專業術語的內容",
            "第四段具有重要信息的文字",
            "最後一段總結性的內容"
        ]
        
        mapped_one_to_one = generator._one_to_one_mapping(whisper_segments, user_sentences)
        logger.info(f"一對一映射結果 ({len(mapped_one_to_one)} 個片段):")
        for i, segment in enumerate(mapped_one_to_one):
            logger.info(f"  {i+1}: {segment['start']:.1f}s-{segment['end']:.1f}s: {segment['text'][:30]}...")
        
        logger.info("📄 測試頁面對片段映射策略...")
        user_pages = [
            "第一頁的完整內容，包含了詳細的說明和介紹。",
            "第二頁討論了相關的技術細節和實現方法。",
            "第三頁總結了前面的內容並提出了結論。"
        ]
        
        mapped_page_to_segment = generator._page_to_segment_mapping(whisper_segments[:3], user_pages)
        logger.info(f"頁面對片段映射結果 ({len(mapped_page_to_segment)} 個片段):")
        for i, segment in enumerate(mapped_page_to_segment):
            logger.info(f"  {i+1}: {segment['start']:.1f}s-{segment['end']:.1f}s: {segment['text'][:30]}...")
        
        # 測試 SRT 生成
        logger.info("📄 測試 SRT 內容生成...")
        srt_content = generator._generate_srt_content(mapped_one_to_one[:3])  # 只測試前3個
        
        logger.info("📄 生成的 SRT 內容：")
        logger.info(srt_content)
        
        # 測試時間格式化
        logger.info("🕒 測試時間格式化...")
        test_times = [0.0, 5.2, 67.555, 3661.789]
        for time_val in test_times:
            formatted = generator._format_time(time_val)
            logger.info(f"  {time_val}s -> {formatted}")
        
        logger.info("✅ 所有功能測試通過！")
        return True
        
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
        from api.whisper_LLM_api import ImprovedHybridSubtitleGenerator as APIImprovedHybrid
        
        if APIImprovedHybrid is not None:
            logger.info("✅ API 中的改進混合字幕生成器可用")
        else:
            logger.warning("⚠️ API 中的改進混合字幕生成器不可用")
            return False
        
        # 測試基本創建
        generator = APIImprovedHybrid(model_size="tiny", traditional_chinese=False)
        logger.info("✅ 通過 API 創建改進混合字幕生成器成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ API 集成測試失敗: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 開始改進混合字幕生成器測試...")
    
    success = True
    
    # 測試基本功能
    if not test_improved_hybrid_subtitle_generator():
        success = False
    
    # 測試 API 集成
    if not test_api_integration():
        success = False
    
    if success:
        logger.info("🎉 所有測試通過！改進的混合字幕系統已準備就緒。")
        logger.info("💡 主要改進：")
        logger.info("  - 智能時間戳映射：根據內容數量選擇最佳映射策略")
        logger.info("  - 句子級別分割：更精確的文字分段")
        logger.info("  - 多種映射策略：一對一、頁面對片段、比例分配")
        logger.info("  - 更好的時間戳利用：充分利用 Whisper 的精確時間信息")
        logger.info("  - 用戶文字優先：使用用戶編輯的正確內容")
    else:
        logger.error("💥 部分測試失敗，請檢查錯誤訊息。")
    
    sys.exit(0 if success else 1)
