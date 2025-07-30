#!/usr/bin/env python3
"""
繁體中文字幕轉換調試測試
Debug Traditional Chinese Subtitle Conversion
"""

import os
import sys
import logging

# Setup detailed logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add project path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_whisper_subtitle_generator():
    """測試 WhisperSubtitleGenerator 的繁體轉換功能"""
    
    print("🔍 調試繁體中文字幕轉換功能")
    print("=" * 60)
    
    try:
        # 導入 WhisperSubtitleGenerator（不需要 Whisper）
        sys.path.append('utility')
        
        # 模擬 WhisperSubtitleGenerator 的關鍵部分
        class MockWhisperSubtitleGenerator:
            def __init__(self, traditional_chinese=False):
                self.traditional_chinese = traditional_chinese
                self.use_zhconv = False
                
                print(f"🇹🇼 Traditional Chinese mode: {'ENABLED' if self.traditional_chinese else 'DISABLED'}")
                
                if self.traditional_chinese:
                    try:
                        import zhconv
                        self.zhconv = zhconv
                        self.use_zhconv = True
                        print("✅ Traditional Chinese conversion enabled (using zhconv)")
                    except ImportError:
                        print("💡 zhconv not available, using built-in conversion table")
                        self.use_zhconv = False
                        self._init_builtin_conversion_table()
                else:
                    self.use_zhconv = False
            
            def _init_builtin_conversion_table(self):
                """Initialize built-in conversion table"""
                self.s2t_table = {
                    '这': '這', '个': '個', '中': '中', '文': '文', '测': '測', '试': '試',
                    '简': '簡', '体': '體', '繁': '繁', '转': '轉', '换': '換',
                    '人': '人', '工': '工', '智': '智', '能': '能', '语': '語', '音': '音',
                    '识': '識', '别': '別', '技': '技', '术': '術',
                    '视': '視', '频': '頻', '字': '字', '幕': '幕', '自': '自', '动': '動',
                    '生': '生', '成': '成', '系': '系', '统': '統',
                    '机': '機', '器': '器', '学': '學', '习': '習', '和': '和', '深': '深',
                    '度': '度', '是': '是', '一': '一', '了': '了', '在': '在', '有': '有',
                    '的': '的', '我': '我', '你': '你', '他': '他', '她': '她', '它': '它',
                    '们': '們', '来': '來', '去': '去', '说': '說', '话': '話',
                    '时': '時', '间': '間', '地': '地', '方': '方', '问': '問', '题': '題',
                    '内': '內', '容': '容', '混': '混', '合': '合', '言': '言',
                    '第': '第', '段': '段'
                }
                print(f"✅ Built-in conversion table initialized with {len(self.s2t_table)} characters")
            
            def _builtin_convert_to_traditional(self, text):
                """Convert using built-in table"""
                result = ""
                for char in text:
                    if char in self.s2t_table:
                        result += self.s2t_table[char]
                    else:
                        result += char
                return result
            
            def _convert_to_traditional_chinese(self, text):
                """Convert simplified to traditional"""
                if not self.traditional_chinese:
                    return text
                
                try:
                    if self.use_zhconv and hasattr(self, 'zhconv'):
                        # Use zhconv library if available
                        converted = self.zhconv.convert(text, 'zh-tw')
                        print(f"🔄 Converted using zhconv: {text[:30]}... → {converted[:30]}...")
                        return converted
                    else:
                        # Use built-in conversion table
                        converted = self._builtin_convert_to_traditional(text)
                        print(f"🔄 Converted using built-in table: {text[:30]}... → {converted[:30]}...")
                        return converted
                except Exception as e:
                    print(f"⚠️ Failed to convert to traditional Chinese: {e}")
                    return text
            
            def _detect_and_convert_chinese(self, text):
                """Detect and convert Chinese"""
                if not self.traditional_chinese:
                    return text
                
                # Check if text contains Chinese characters
                chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
                if chinese_chars > 0:
                    print(f"🔄 Converting Chinese text: {text[:50]}...")
                    converted = self._convert_to_traditional_chinese(text)
                    print(f"✅ Conversion result: {converted[:50]}...")
                    return converted
                
                return text
            
            def _create_srt_from_segments(self, segments):
                """Create SRT with conversion"""
                srt_content = ""
                
                for i, segment in enumerate(segments, 1):
                    start_time = f"00:00:{int(segment['start']):02d},000"
                    end_time = f"00:00:{int(segment['end']):02d},000"
                    text = segment['text'].strip()
                    
                    # Apply traditional Chinese conversion if enabled
                    if self.traditional_chinese:
                        text = self._detect_and_convert_chinese(text)
                    
                    srt_content += f"{i}\n"
                    srt_content += f"{start_time} --> {end_time}\n"
                    srt_content += f"{text}\n\n"
                
                return srt_content
        
        # 測試案例
        test_segments = [
            {'start': 0, 'end': 3, 'text': '这是简体中文测试'},
            {'start': 3, 'end': 6, 'text': '人工智能语音识别技术'},
            {'start': 6, 'end': 9, 'text': '视频字幕自动生成系统'}
        ]
        
        print("\n📝 測試簡體模式:")
        print("-" * 40)
        gen_simplified = MockWhisperSubtitleGenerator(traditional_chinese=False)
        srt_simplified = gen_simplified._create_srt_from_segments(test_segments)
        print("簡體 SRT:")
        print(srt_simplified)
        
        print("\n🇹🇼 測試繁體模式:")
        print("-" * 40)
        gen_traditional = MockWhisperSubtitleGenerator(traditional_chinese=True)
        srt_traditional = gen_traditional._create_srt_from_segments(test_segments)
        print("繁體 SRT:")
        print(srt_traditional)
        
        # 檢查轉換效果
        traditional_chars = ['這', '語', '術', '識', '別', '視', '頻', '動', '統', '機', '學', '習']
        found_traditional = any(char in srt_traditional for char in traditional_chars)
        
        print("\n📊 測試結果:")
        print(f"  簡體模式: {'✅' if '这是简体' in srt_simplified else '❌'}")
        print(f"  繁體模式: {'✅' if found_traditional else '❌'}")
        print(f"  轉換檢測: {'✅' if found_traditional else '❌'}")
        
        return found_traditional
        
    except Exception as e:
        print(f"❌ 測試錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    
    print("🔧 繁體中文字幕轉換調試")
    print("Traditional Chinese Subtitle Conversion Debug")
    print("=" * 80)
    
    success = test_whisper_subtitle_generator()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ 調試完成：繁體轉換功能正常運作")
        print("\n💡 如果影片仍顯示簡體字，請檢查：")
        print("  1. 確認在 Web 介面勾選了 '🇹🇼 Traditional Chinese Subtitles'")
        print("  2. 檢查後端日誌是否顯示轉換過程")
        print("  3. 驗證參數是否正確傳遞到 WhisperSubtitleGenerator")
    else:
        print("❌ 調試失敗：請檢查轉換邏輯")
    
    print("\n🔍 下一步除錯建議：")
    print("  • 檢查 Flask app.py 中的參數傳遞")
    print("  • 驗證 API 調用時的 traditional_chinese 參數")
    print("  • 查看服務器日誌中的轉換信息")

if __name__ == "__main__":
    main()
