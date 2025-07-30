#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 測試擴充後的繁體中文轉換表
這個腳本用來測試從日誌中發現的轉換問題是否已解決
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utility.whisper_subtitle import WhisperSubtitleGenerator

def test_conversion():
    print("🚀 測試擴充後的繁體中文轉換表")
    print("=" * 60)
    
    try:
        # 創建測試實例（使用測試模式）
        generator = WhisperSubtitleGenerator(traditional_chinese=True)
        
        # 從日誌中提取的測試文本
        test_texts = [
            "好的,这张投影片主要讲述的是AI市场的蓬勃发展以及AI与资料库结合的趋势。",
            "首先,可以看到AI市场的规模正在快速扩张。",
            "2023年,全球市场已经达到1966年3月亿美元,预计到2030年将突破2万亿美元,年增长率高达36",
            "这说明了,AI技术正在被越来越多的企业所接受和应用。",
            "同时,像是Google、微软、Apple这些科技巨头也在积极投资AI,这也进一步推动了AI在企业应用",
            "另外一个重点是AI与资料库的结合。",
            "根据IDC的预测,到2026年,全球将有超过40%的企业部署智能资料库,利用AI来自动画资料清理、预",
            "这代表了AI在资料管理领域具有巨大的潜力。",
            "简单来说,NLQ让大家可以用日常用语来查询资料库,不用再学复杂的CQL语法。",
            "这有几个好处,首先,它降低了技术门槛,让不熟悉城市的同人也能自己查询资料。"
        ]
        
        print("📝 測試文本轉換結果：")
        print()
        
        for i, text in enumerate(test_texts, 1):
            print(f"📄 測試 {i}:")
            print(f"  原文: {text}")
            
            # 使用內部轉換方法
            converted = generator._convert_to_traditional_chinese(text)
            print(f"  轉換: {converted}")
            
            # 計算轉換率
            original_chars = [c for c in text if '\u4e00' <= c <= '\u9fff']  # 中文字符
            converted_chars = [c for c in converted if '\u4e00' <= c <= '\u9fff']
            
            if original_chars:
                changes = sum(1 for o, c in zip(original_chars, converted_chars) if o != c)
                conversion_rate = (changes / len(original_chars)) * 100
                print(f"  轉換率: {conversion_rate:.1f}% ({changes}/{len(original_chars)} 字符)")
            
            print()
        
        # 測試特定字符轉換
        print("🔍 特定字符轉換測試：")
        problem_chars = ['张', '讲', '述', '发', '展', '资', '料', '库', '结', '合', '趋', '势']
        
        for char in problem_chars:
            converted = generator._convert_to_traditional_chinese(char)
            status = "✅" if char != converted else "❌"
            print(f"  {status} '{char}' → '{converted}'")
        
        print()
        print("🎉 轉換表測試完成！")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_conversion()
