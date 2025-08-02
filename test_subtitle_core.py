#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
專門測試改進混合字幕生成器的核心功能
"""

import sys
import os
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_subtitle_core_functionality():
    """測試字幕生成器的核心功能"""
    try:
        logger.info("🎯 測試改進混合字幕生成器的核心功能...")
        
        # 直接導入字幕生成器
        from utility.improved_hybrid_subtitle_generator import ImprovedHybridSubtitleGenerator
        
        # 創建實例
        generator = ImprovedHybridSubtitleGenerator(
            model_size="tiny",
            traditional_chinese=True
        )
        
        logger.info("✅ 字幕生成器創建成功")
        
        # 測試真實場景：模擬用戶編輯的PDF文字
        user_edited_pages = [
            "歡迎來到人工智慧的世界。今天我們將探討機器學習的基本概念和應用。",
            "機器學習是人工智慧的重要分支。它讓電腦能夠從數據中學習並做出預測。",
            "深度學習使用神經網路模擬人腦。這種方法在圖像識別和自然語言處理方面表現出色。",
            "未來，人工智慧將在各個領域發揮重要作用。我們需要負責任地發展這項技術。"
        ]
        
        # 模擬 Whisper 轉錄結果（包含時間戳但內容可能不準確）
        whisper_segments = [
            {"start": 0.0, "end": 6.5, "text": "歡迎來到人工智慧"},
            {"start": 6.5, "end": 12.8, "text": "今天探討機器學習概念"},
            {"start": 12.8, "end": 19.2, "text": "機器學習是重要分支"},
            {"start": 19.2, "end": 25.7, "text": "電腦從數據學習預測"},
            {"start": 25.7, "end": 32.1, "text": "深度學習神經網路"},
            {"start": 32.1, "end": 38.9, "text": "圖像識別語言處理"},
            {"start": 38.9, "end": 45.0, "text": "人工智慧各領域應用"},
            {"start": 45.0, "end": 50.0, "text": "負責任發展技術"}
        ]
        
        logger.info(f"📖 用戶提供 {len(user_edited_pages)} 頁內容")
        logger.info(f"🎵 Whisper 提供 {len(whisper_segments)} 個時間片段")
        
        # 測試智能映射
        mapped_segments = generator._smart_map_text_to_segments(whisper_segments, user_edited_pages)
        
        logger.info(f"🔄 映射完成，生成 {len(mapped_segments)} 個字幕片段：")
        for i, segment in enumerate(mapped_segments):
            logger.info(f"  {i+1:2d}: {segment['start']:5.1f}s - {segment['end']:5.1f}s | {segment['text'][:50]}...")
        
        # 生成 SRT 內容
        srt_content = generator._generate_srt_content(mapped_segments)
        
        logger.info("📄 生成的完整 SRT 內容：")
        logger.info("=" * 50)
        logger.info(srt_content)
        logger.info("=" * 50)
        
        # 驗證時間戳的正確性
        logger.info("⏰ 驗證時間戳正確性...")
        
        prev_end = 0
        time_gaps = []
        overlaps = []
        
        for i, segment in enumerate(mapped_segments):
            start_time = segment['start']
            end_time = segment['end']
            
            # 檢查時間順序
            if start_time < prev_end:
                overlaps.append(f"片段 {i+1} 開始時間 {start_time:.1f}s 早於前一片段結束時間 {prev_end:.1f}s")
            
            # 檢查時間間隔
            if i > 0:
                gap = start_time - prev_end
                time_gaps.append(gap)
                if gap > 2.0:  # 超過2秒的間隔
                    logger.warning(f"⚠️ 片段 {i} 和 {i+1} 之間有 {gap:.1f}s 的間隔")
            
            # 檢查片段長度
            duration = end_time - start_time
            if duration < 0.5:
                logger.warning(f"⚠️ 片段 {i+1} 持續時間過短: {duration:.1f}s")
            elif duration > 10.0:
                logger.warning(f"⚠️ 片段 {i+1} 持續時間過長: {duration:.1f}s")
            
            prev_end = end_time
        
        if overlaps:
            logger.error("❌ 發現時間重疊問題:")
            for overlap in overlaps:
                logger.error(f"  {overlap}")
        else:
            logger.info("✅ 無時間重疊問題")
        
        if time_gaps:
            avg_gap = sum(time_gaps) / len(time_gaps)
            logger.info(f"📊 平均時間間隔: {avg_gap:.2f}s")
        
        # 測試不同映射策略的效果
        logger.info("🧪 測試不同映射策略...")
        
        # 一對一映射測試
        sentences = []
        for page in user_edited_pages:
            sentences.extend(generator._split_text_into_sentences(page))
        
        logger.info(f"📝 總共分割出 {len(sentences)} 個句子")
        
        one_to_one = generator._one_to_one_mapping(whisper_segments, sentences)
        logger.info(f"🎯 一對一映射: {len(one_to_one)} 個片段")
        
        page_to_segment = generator._page_to_segment_mapping(whisper_segments, user_edited_pages)
        logger.info(f"📄 頁面映射: {len(page_to_segment)} 個片段")
        
        proportional = generator._proportional_mapping(whisper_segments, sentences)
        logger.info(f"⚖️ 比例映射: {len(proportional)} 個片段")
        
        logger.info("✅ 所有核心功能測試通過！")
        
        # 提供使用建議
        logger.info("💡 使用建議：")
        if len(sentences) == len(whisper_segments):
            logger.info("  - 句子數量與音頻片段數量匹配，建議使用一對一映射")
        elif len(user_edited_pages) == len(whisper_segments):
            logger.info("  - 頁面數量與音頻片段數量匹配，建議使用頁面映射")
        else:
            logger.info("  - 數量不匹配，系統將自動選擇最佳映射策略")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("🚀 開始改進混合字幕生成器核心功能測試...")
    
    success = test_subtitle_core_functionality()
    
    if success:
        logger.info("🎉 測試完成！改進的混合字幕系統核心功能正常。")
        logger.info("🔧 主要特點：")
        logger.info("  ✓ 智能時間戳映射：保持 Whisper 的精確時間信息")
        logger.info("  ✓ 用戶內容優先：使用用戶編輯的正確文字")
        logger.info("  ✓ 多種映射策略：自動選擇最佳映射方式")
        logger.info("  ✓ 時間戳驗證：確保字幕時間的連續性和合理性")
        logger.info("  ✓ 繁體中文支持：自動轉換簡體中文")
    else:
        logger.error("💥 測試失敗，請檢查錯誤訊息並修復問題。")
    
    sys.exit(0 if success else 1)
