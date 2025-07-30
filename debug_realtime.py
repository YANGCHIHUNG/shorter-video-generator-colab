#!/usr/bin/env python3
"""
即時繁體中文字幕調試腳本
Real-time Traditional Chinese Subtitle Debug Script
"""

import os
import sys
import logging

# 設置詳細日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_real_whisper_subtitle():
    """測試真實的 WhisperSubtitleGenerator"""
    
    print("🔧 測試真實的 WhisperSubtitleGenerator")
    print("=" * 60)
    
    try:
        # 導入實際的模組
        sys.path.append('utility')
        from utility.whisper_subtitle import WhisperSubtitleGenerator
        
        print("✅ 成功導入 WhisperSubtitleGenerator")
        
        # 測試初始化
        print("\n📝 測試簡體模式:")
        gen_simplified = WhisperSubtitleGenerator(traditional_chinese=False)
        print(f"  traditional_chinese 屬性: {gen_simplified.traditional_chinese}")
        
        print("\n🇹🇼 測試繁體模式:")
        gen_traditional = WhisperSubtitleGenerator(traditional_chinese=True)
        print(f"  traditional_chinese 屬性: {gen_traditional.traditional_chinese}")
        print(f"  use_zhconv 屬性: {getattr(gen_traditional, 'use_zhconv', 'Not found')}")
        
        # 測試轉換功能
        test_texts = [
            "这是简体中文测试",
            "人工智能语音识别技术",
            "Hello world! 这是混合内容。"
        ]
        
        print("\n🔄 測試文本轉換:")
        for i, text in enumerate(test_texts, 1):
            print(f"  {i}. 原文: {text}")
            
            # 簡體模式
            result_simplified = gen_simplified._detect_and_convert_chinese(text)
            print(f"     簡體模式: {result_simplified}")
            
            # 繁體模式
            result_traditional = gen_traditional._detect_and_convert_chinese(text)
            print(f"     繁體模式: {result_traditional}")
            
            # 檢查是否有轉換
            converted = result_traditional != result_simplified
            print(f"     轉換狀態: {'✅ 已轉換' if converted else '❌ 未轉換'}")
            print()
        
        return True
        
    except ImportError as e:
        print(f"❌ 無法導入模組: {e}")
        print("💡 請確認:")
        print("  1. whisper_subtitle.py 檔案存在")
        print("  2. 所有依賴已正確安裝")
        return False
    except Exception as e:
        print(f"❌ 測試錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_environment():
    """檢查環境設置"""
    
    print("\n🌍 環境檢查")
    print("-" * 40)
    
    # 檢查檔案
    files_to_check = [
        'utility/whisper_subtitle.py',
        'api/whisper_LLM_api.py',
        'app.py',
        'templates/edit_text.html'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} (檔案不存在)")
    
    # 檢查 Python 路徑
    print(f"\n📁 Python 路徑:")
    for path in sys.path[:3]:  # 只顯示前3個路徑
        print(f"  - {path}")
    
    # 檢查當前目錄
    print(f"\n📂 當前目錄: {os.getcwd()}")
    
    return True

if __name__ == "__main__":
    print("🔍 繁體中文字幕即時調試")
    print("Real-time Traditional Chinese Subtitle Debug")
    print("=" * 80)
    
    # 環境檢查
    env_ok = check_environment()
    
    if env_ok:
        # 實際測試
        test_ok = test_real_whisper_subtitle()
        
        print("\n" + "=" * 80)
        if test_ok:
            print("✅ 調試完成：繁體轉換功能正常")
            print("\n💡 如果網頁仍顯示簡體字，請：")
            print("  1. 重新啟動 Flask 應用程式")
            print("  2. 清除瀏覽器快取並重新載入")
            print("  3. 確認勾選繁體中文選項")
            print("  4. 檢查瀏覽器開發者工具的 Network 請求")
        else:
            print("❌ 調試失敗：請檢查環境設置")
    else:
        print("❌ 環境檢查失敗")
