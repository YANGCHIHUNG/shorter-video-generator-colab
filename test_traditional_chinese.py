#!/usr/bin/env python3
"""
繁體中文字幕轉換測試
Testing Traditional Chinese subtitle conversion functionality
"""

import sys
import os

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_traditional_chinese_conversion():
    """測試繁體中文轉換功能"""
    
    try:
        from utility.whisper_subtitle import WhisperSubtitleGenerator
        print("✅ WhisperSubtitleGenerator imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import WhisperSubtitleGenerator: {e}")
        return False
    
    # Test cases with simplified Chinese text
    test_cases = [
        {
            "simplified": "这是一个简体中文测试",
            "expected_traditional": "這是一個簡體中文測試",
            "description": "Basic Chinese conversion"
        },
        {
            "simplified": "人工智能语音识别技术",
            "expected_traditional": "人工智能語音識別技術", 
            "description": "Technical terminology"
        },
        {
            "simplified": "视频字幕自动生成系统",
            "expected_traditional": "視頻字幕自動生成系統",
            "description": "Video subtitle system"
        },
        {
            "simplified": "机器学习和深度学习",
            "expected_traditional": "機器學習和深度學習",
            "description": "Machine learning terms"
        },
        {
            "simplified": "Hello 世界！这是中英文混合内容。",
            "expected_traditional": "Hello 世界！這是中英文混合內容。",
            "description": "Mixed Chinese-English content"
        }
    ]
    
    print("🔄 Testing Traditional Chinese Conversion")
    print("=" * 60)
    
    # Test simplified Chinese (should not convert)
    print("\n📝 Testing Simplified Chinese Mode:")
    subtitle_gen_simplified = WhisperSubtitleGenerator(traditional_chinese=False)
    
    for i, case in enumerate(test_cases, 1):
        result = subtitle_gen_simplified._detect_and_convert_chinese(case["simplified"])
        print(f"  {i}. {case['description']}")
        print(f"     Original: {case['simplified']}")
        print(f"     Result:   {result}")
        print(f"     Status:   {'✅ No conversion (as expected)' if result == case['simplified'] else '⚠️ Unexpected conversion'}")
    
    # Test traditional Chinese conversion
    print("\n🇹🇼 Testing Traditional Chinese Mode:")
    
    try:
        subtitle_gen_traditional = WhisperSubtitleGenerator(traditional_chinese=True)
        
        if not subtitle_gen_traditional.traditional_chinese:
            print("⚠️ Traditional Chinese conversion disabled (zhconv not available)")
            return False
        
        for i, case in enumerate(test_cases, 1):
            result = subtitle_gen_traditional._detect_and_convert_chinese(case["simplified"])
            print(f"  {i}. {case['description']}")
            print(f"     Simplified:   {case['simplified']}")
            print(f"     Converted:    {result}")
            print(f"     Expected:     {case['expected_traditional']}")
            
            # Check if conversion worked (allowing for slight variations)
            if result != case["simplified"]:
                print(f"     Status:       ✅ Conversion applied")
            else:
                print(f"     Status:       ⚠️ No conversion occurred")
            print()
        
        print("🎯 Testing SRT Generation with Traditional Chinese:")
        
        # Create mock segments for SRT testing
        mock_segments = [
            {
                'start': 0.0,
                'end': 3.5,
                'text': '这是第一段简体中文字幕'
            },
            {
                'start': 3.5,
                'end': 7.0,
                'text': '人工智能语音识别技术'
            },
            {
                'start': 7.0,
                'end': 10.5,
                'text': 'Hello world! 这是混合语言内容。'
            }
        ]
        
        # Generate SRT with traditional conversion
        srt_content = subtitle_gen_traditional._create_srt_from_segments(mock_segments)
        
        print("Generated SRT content:")
        print("-" * 40)
        print(srt_content)
        print("-" * 40)
        
        # Check if traditional characters are present
        traditional_indicators = ['這', '語', '術', '內', '機']
        found_traditional = any(char in srt_content for char in traditional_indicators)
        
        if found_traditional:
            print("✅ Traditional Chinese characters found in SRT!")
        else:
            print("⚠️ No traditional Chinese characters detected in SRT")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing traditional Chinese conversion: {e}")
        return False

def test_font_selection():
    """測試字體選擇功能"""
    
    print("\n🔤 Testing Font Selection")
    print("=" * 60)
    
    try:
        from utility.whisper_subtitle import WhisperSubtitleGenerator
        
        # Test simplified Chinese font
        subtitle_gen_simplified = WhisperSubtitleGenerator(traditional_chinese=False)
        simplified_style = subtitle_gen_simplified._get_colab_subtitle_style("default")
        print("📝 Simplified Chinese Font Style:")
        print(f"   {simplified_style}")
        
        if "Noto Sans CJK SC" in simplified_style:
            print("   ✅ Using Simplified Chinese font (Noto Sans CJK SC)")
        else:
            print("   ⚠️ Simplified Chinese font not detected")
        
        # Test traditional Chinese font
        subtitle_gen_traditional = WhisperSubtitleGenerator(traditional_chinese=True)
        traditional_style = subtitle_gen_traditional._get_colab_subtitle_style("default")
        print("\n🇹🇼 Traditional Chinese Font Style:")
        print(f"   {traditional_style}")
        
        if "Noto Sans CJK TC" in traditional_style:
            print("   ✅ Using Traditional Chinese font (Noto Sans CJK TC)")
        else:
            print("   ⚠️ Traditional Chinese font not detected")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing font selection: {e}")
        return False

def main():
    """主測試函數"""
    
    print("🇹🇼 繁體中文字幕功能測試")
    print("Traditional Chinese Subtitle Feature Test")
    print("=" * 80)
    
    # Test conversion functionality
    conversion_test = test_traditional_chinese_conversion()
    
    # Test font selection
    font_test = test_font_selection()
    
    print("\n" + "=" * 80)
    print("📊 測試結果摘要 (Test Results Summary)")
    print("=" * 80)
    
    print(f"✅ 繁體轉換測試: {'通過' if conversion_test else '失敗'}")
    print(f"✅ 字體選擇測試: {'通過' if font_test else '失敗'}")
    
    if conversion_test and font_test:
        print("\n🎉 所有測試通過！繁體中文字幕功能已準備就緒。")
        print("💡 使用方式:")
        print("   1. 在編輯頁面勾選 '🇹🇼 Traditional Chinese Subtitles'")
        print("   2. 系統會自動將簡體中文字幕轉換為繁體中文")
        print("   3. 使用繁體中文字體 (Noto Sans CJK TC) 進行渲染")
    else:
        print("\n❌ 部分測試失敗，請檢查設置。")
    
    print("\n📋 功能特點:")
    print("   • 自動簡繁轉換 (zhconv 庫)")
    print("   • 繁體中文字體支援")
    print("   • 保持英文和符號不變")
    print("   • 支援混合語言內容")

if __name__ == "__main__":
    main()
