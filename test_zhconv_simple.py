#!/usr/bin/env python3
"""
簡化版繁體中文轉換測試
Simple Traditional Chinese conversion test without Whisper dependency
"""

def test_zhconv_installation():
    """測試 zhconv 庫是否正確安裝"""
    
    try:
        import zhconv
        print("✅ zhconv library imported successfully")
        return zhconv
    except ImportError as e:
        print(f"❌ Failed to import zhconv: {e}")
        return None

def test_conversion_directly():
    """直接測試簡繁轉換功能"""
    
    zhconv = test_zhconv_installation()
    if not zhconv:
        return False
    
    # Test cases
    test_cases = [
        {
            "simplified": "这是一个简体中文测试",
            "expected_keywords": ["這", "個", "測", "試"],
            "description": "Basic Chinese conversion"
        },
        {
            "simplified": "人工智能语音识别技术",
            "expected_keywords": ["語", "術", "識"],
            "description": "Technical terminology"
        },
        {
            "simplified": "视频字幕自动生成系统",
            "expected_keywords": ["視", "頻", "幕", "動", "統"],
            "description": "Video subtitle system"
        },
        {
            "simplified": "机器学习和深度学习",
            "expected_keywords": ["機", "學", "習"],
            "description": "Machine learning terms"
        },
        {
            "simplified": "Hello 世界！这是中英文混合内容。",
            "expected_keywords": ["這", "內", "容"],
            "description": "Mixed Chinese-English content"
        }
    ]
    
    print("🔄 Testing Direct zhconv Conversion")
    print("=" * 60)
    
    all_passed = True
    
    for i, case in enumerate(test_cases, 1):
        try:
            # Convert using zhconv
            converted = zhconv.convert(case["simplified"], 'zh-tw')
            
            print(f"  {i}. {case['description']}")
            print(f"     簡體: {case['simplified']}")
            print(f"     繁體: {converted}")
            
            # Check if conversion worked
            found_traditional = any(keyword in converted for keyword in case["expected_keywords"])
            
            if found_traditional and converted != case["simplified"]:
                print(f"     狀態: ✅ 轉換成功")
            else:
                print(f"     狀態: ⚠️ 轉換可能有問題")
                all_passed = False
            
            print()
            
        except Exception as e:
            print(f"     狀態: ❌ 轉換錯誤: {e}")
            all_passed = False
    
    return all_passed

def test_conversion_class_simulation():
    """模擬字幕生成器的轉換邏輯"""
    
    zhconv = test_zhconv_installation()
    if not zhconv:
        return False
    
    print("🎯 Testing Subtitle Generator Conversion Logic")
    print("=" * 60)
    
    # Simulate the conversion methods
    def convert_to_traditional_chinese(text: str, traditional_chinese: bool = True) -> str:
        """模擬 _convert_to_traditional_chinese 方法"""
        if not traditional_chinese:
            return text
        
        try:
            converted = zhconv.convert(text, 'zh-tw')
            return converted
        except Exception as e:
            print(f"⚠️ Failed to convert to traditional Chinese: {e}")
            return text
    
    def detect_and_convert_chinese(text: str, traditional_chinese: bool = True) -> str:
        """模擬 _detect_and_convert_chinese 方法"""
        if not traditional_chinese:
            return text
        
        # Check if text contains Chinese characters
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        if chinese_chars > 0:
            print(f"🔄 Converting Chinese text: {text[:50]}...")
            return convert_to_traditional_chinese(text, traditional_chinese)
        
        return text
    
    def create_srt_from_segments(segments, traditional_chinese: bool = True):
        """模擬 _create_srt_from_segments 方法"""
        srt_content = ""
        
        for i, segment in enumerate(segments, 1):
            start_time = f"{int(segment['start']//3600):02d}:{int((segment['start']%3600)//60):02d}:{segment['start']%60:06.3f}".replace('.', ',')
            end_time = f"{int(segment['end']//3600):02d}:{int((segment['end']%3600)//60):02d}:{segment['end']%60:06.3f}".replace('.', ',')
            text = segment['text'].strip()
            
            # Apply traditional Chinese conversion if enabled
            if traditional_chinese:
                text = detect_and_convert_chinese(text, traditional_chinese)
            
            srt_content += f"{i}\n"
            srt_content += f"{start_time} --> {end_time}\n"
            srt_content += f"{text}\n\n"
        
        return srt_content
    
    # Test with mock segments
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
    
    # Test simplified mode (no conversion)
    print("📝 Simplified Chinese Mode (No Conversion):")
    srt_simplified = create_srt_from_segments(mock_segments, traditional_chinese=False)
    print("Generated SRT:")
    print("-" * 40)
    print(srt_simplified[:200] + "..." if len(srt_simplified) > 200 else srt_simplified)
    print("-" * 40)
    
    # Test traditional mode (with conversion)
    print("\n🇹🇼 Traditional Chinese Mode (With Conversion):")
    srt_traditional = create_srt_from_segments(mock_segments, traditional_chinese=True)
    print("Generated SRT:")
    print("-" * 40)
    print(srt_traditional[:300] + "..." if len(srt_traditional) > 300 else srt_traditional)
    print("-" * 40)
    
    # Check for traditional characters
    traditional_indicators = ['這', '語', '術', '內', '機', '識', '頻']
    found_traditional = any(char in srt_traditional for char in traditional_indicators)
    
    if found_traditional:
        print("✅ Traditional Chinese characters found in SRT!")
        return True
    else:
        print("⚠️ No traditional Chinese characters detected in SRT")
        return False

def main():
    """主測試函數"""
    
    print("🇹🇼 繁體中文轉換功能測試 (簡化版)")
    print("Traditional Chinese Conversion Test (Simplified)")
    print("=" * 80)
    
    # Test direct conversion
    direct_test = test_conversion_directly()
    
    # Test simulated class logic
    class_test = test_conversion_class_simulation()
    
    print("\n" + "=" * 80)
    print("📊 測試結果摘要 (Test Results Summary)")
    print("=" * 80)
    
    print(f"✅ 直接轉換測試: {'通過' if direct_test else '失敗'}")
    print(f"✅ 類別邏輯測試: {'通過' if class_test else '失敗'}")
    
    if direct_test and class_test:
        print("\n🎉 所有測試通過！繁體中文轉換功能正常運作！")
        print("\n💡 使用方式:")
        print("   1. 在編輯頁面勾選 '🇹🇼 Traditional Chinese Subtitles'")
        print("   2. 系統會自動將簡體中文字幕轉換為繁體中文")
        print("   3. 使用繁體中文字體進行渲染")
        
        print("\n🔧 技術細節:")
        print("   • 使用 zhconv 庫進行簡繁轉換")
        print("   • 自動檢測中文字符")
        print("   • 保持英文和標點符號不變")
        print("   • 支援混合語言內容")
        
    else:
        print("\n❌ 部分測試失敗，請檢查 zhconv 庫安裝。")
        print("💡 安裝命令: pip install zhconv")

if __name__ == "__main__":
    main()
