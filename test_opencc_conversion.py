#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 專業級繁體中文轉換測試 - 使用 OpenCC
測試 OpenCC 的完整簡繁轉換能力
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utility.whisper_subtitle import WhisperSubtitleGenerator

def test_opencc_conversion():
    print("🚀 專業級繁體中文轉換測試 - OpenCC")
    print("=" * 60)
    
    try:
        # 創建使用 OpenCC 的實例
        generator = WhisperSubtitleGenerator(traditional_chinese=True)
        
        print(f"📊 轉換器類型: {getattr(generator, 'use_converter', 'unknown')}")
        print()
        
        # 更全面的測試文本，包含各種中文內容
        test_texts = [
            # 你日誌中的實際內容
            "好的,这张投影片主要讲述的是AI市场的蓬勃发展以及AI与资料库结合的趋势。",
            "首先,可以看到AI市场的规模正在快速扩张。",
            "2023年,全球市场已经达到1966年3月亿美元,预计到2030年将突破2万亿美元,年增长率高达36%。",
            "这说明了,AI技术正在被越来越多的企业所接受和应用。",
            
            # 技術詞彙測試
            "人工智能、机器学习、深度学习、神经网络、算法优化",
            "数据库、云计算、边缘计算、物联网、区块链技术",
            "自然语言处理、计算机视觉、语音识别、图像识别",
            
            # 商業用語測試
            "市场营销、客户服务、供应链管理、财务管理、风险控制",
            "企业管理、战略规划、业务流程、质量控制、成本优化",
            
            # 教育學術用語
            "教育资源、学习效果、教学质量、课程设计、评估体系",
            "研究方法、实验设计、数据分析、论文发表、学术交流",
            
            # 日常用語測試
            "请问您需要什么帮助？我们会尽快为您处理这个问题。",
            "谢谢您的支持和理解，祝您生活愉快，工作顺利！",
            
            # 複雜句子測試
            "在这个快速发展的信息时代，我们必须不断学习新的技术和知识，才能适应社会的变化和发展需求。",
        ]
        
        print("📝 OpenCC 轉換效果測試：")
        print()
        
        total_chars = 0
        total_converted = 0
        
        for i, text in enumerate(test_texts, 1):
            print(f"📄 測試 {i}:")
            print(f"  原文: {text}")
            
            converted = generator._convert_to_traditional_chinese(text)
            print(f"  轉換: {converted}")
            
            # 計算轉換統計
            original_chars = [c for c in text if '\u4e00' <= c <= '\u9fff']  # 中文字符
            converted_chars = [c for c in converted if '\u4e00' <= c <= '\u9fff']
            
            if original_chars:
                changes = sum(1 for o, c in zip(original_chars, converted_chars) if o != c)
                conversion_rate = (changes / len(original_chars)) * 100 if original_chars else 0
                print(f"  轉換率: {conversion_rate:.1f}% ({changes}/{len(original_chars)} 字符)")
                
                total_chars += len(original_chars)
                total_converted += changes
            
            print()
        
        # 總體統計
        overall_rate = (total_converted / total_chars) * 100 if total_chars > 0 else 0
        print("📊 總體轉換統計：")
        print(f"  總中文字符數: {total_chars}")
        print(f"  已轉換字符數: {total_converted}")
        print(f"  總體轉換率: {overall_rate:.1f}%")
        print()
        
        # 測試特定困難字符
        print("🔍 困難字符轉換測試：")
        difficult_chars = [
            '发', '发展', '发现',  # 發
            '业', '企业', '专业',  # 業
            '经', '已经', '经过',  # 經
            '团', '团队', '集团',  # 團
            '态', '状态', '生态',  # 態
            '万', '万能', '万岁',  # 萬
            '义', '意义', '主义',  # 義
            '华', '中华', '华人',  # 華
            '处', '处理', '好处',  # 處
            '语', '语言', '汉语',  # 語
        ]
        
        for char_or_word in difficult_chars:
            converted = generator._convert_to_traditional_chinese(char_or_word)
            status = "✅" if char_or_word != converted else "❌"
            print(f"  {status} '{char_or_word}' → '{converted}'")
        
        print()
        print("🎉 OpenCC 專業轉換測試完成！")
        
        # 給出建議
        if hasattr(generator, 'use_converter') and generator.use_converter == 'opencc':
            print("✅ 已使用 OpenCC 專業轉換器，轉換效果最佳！")
        elif hasattr(generator, 'use_converter') and generator.use_converter == 'zhconv':
            print("⚠️ 使用 zhconv 轉換器，效果良好但不如 OpenCC 全面")
        else:
            print("❌ 使用內建轉換表，覆蓋範圍有限")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_opencc_conversion()
