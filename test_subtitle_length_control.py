#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試字幕長度控制功能的腳本

用於驗證不同長度模式下字幕切分的效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utility.improved_hybrid_subtitle_generator import ImprovedHybridSubtitleGenerator

def test_subtitle_length_control():
    """測試不同字幕長度控制模式"""
    print("📏 測試字幕長度控制系統")
    print("=" * 60)
    
    # 測試數據 - 包含不同長度的文字
    test_texts = [
        "這是一個短句子。",
        "這是一個中等長度的句子，包含了更多的文字內容。",
        "這是一個非常長的句子，包含了大量的文字內容，用於測試字幕切分功能是否能夠正確地將過長的文字分割成適合顯示的片段，確保觀眾能夠清楚地閱讀字幕內容。",
        "專業技術術語測試：人工智慧機器學習深度學習神經網路自然語言處理計算機視覺語音識別資料科學演算法最佳化。"
    ]
    
    # 測試不同的長度模式
    length_modes = [
        ("compact", "緊湊模式 - 每行12字"),
        ("standard", "標準模式 - 每行15字"),
        ("relaxed", "寬鬆模式 - 每行18字"),
        ("auto", "自動模式 - 智能選擇")
    ]
    
    for mode, description in length_modes:
        print(f"\n🎛️ 測試 {description}")
        print("-" * 50)
        
        try:
            # 創建字幕生成器
            generator = ImprovedHybridSubtitleGenerator(
                model_size="small",
                traditional_chinese=True,
                subtitle_length_mode=mode
            )
            
            print(f"   配置: 每行{generator.max_chars_per_line}字，最多{generator.max_lines}行")
            print(f"   總字元限制: {generator.max_chars_total}字")
            print(f"   最小顯示時間: {generator.min_display_time}秒")
            
            # 測試每個文字
            for i, text in enumerate(test_texts, 1):
                print(f"\n   📝 測試文字 {i} (長度: {len(text)}字):")
                print(f"      原文: {text[:50]}{'...' if len(text) > 50 else ''}")
                
                # 模擬時間軸 (每個文字2秒)
                start_time = (i - 1) * 2.0
                end_time = i * 2.0
                
                # 切分字幕
                split_subtitles = generator._split_long_subtitle(text, start_time, end_time)
                
                print(f"      切分結果: {len(split_subtitles)} 個片段")
                
                for j, subtitle in enumerate(split_subtitles, 1):
                    duration = subtitle["end"] - subtitle["start"]
                    # 顯示切分後的文字，用 \\n 表示換行
                    display_text = subtitle["text"].replace('\n', '\\n')
                    print(f"         片段{j}: {subtitle['start']:.1f}s-{subtitle['end']:.1f}s ({duration:.1f}s)")
                    print(f"                '{display_text}'")
                    print(f"                長度: {len(subtitle['text'].replace(chr(10), ''))}字")
            
        except Exception as e:
            print(f"❌ 測試失敗: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 字幕長度控制測試完成")

def test_line_formatting():
    """測試行格式化功能"""
    print("\n📐 測試行格式化功能")
    print("=" * 60)
    
    test_cases = [
        ("短文字", "這是短文字"),
        ("中等長度", "這是一個中等長度的文字測試"),
        ("需要換行", "這是一個需要換行顯示的較長文字內容測試"),
        ("強制切分", "這是一個非常長的文字需要強制切分成多行來確保顯示效果")
    ]
    
    for mode in ["compact", "standard", "relaxed"]:
        print(f"\n🎛️ {mode.upper()} 模式測試:")
        
        generator = ImprovedHybridSubtitleGenerator(
            subtitle_length_mode=mode
        )
        
        for case_name, text in test_cases:
            formatted = generator._format_subtitle_lines(text, generator.max_chars_per_line)
            lines = formatted.split('\n')
            
            print(f"   {case_name}: '{text}' ({len(text)}字)")
            print(f"      格式化結果: {len(lines)}行")
            for i, line in enumerate(lines, 1):
                print(f"         第{i}行: '{line}' ({len(line)}字)")

if __name__ == "__main__":
    test_subtitle_length_control()
    test_line_formatting()
    print("\n🎉 所有測試完成！")
