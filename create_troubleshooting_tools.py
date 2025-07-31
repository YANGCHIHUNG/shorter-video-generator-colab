#!/usr/bin/env python3
"""
繁體中文字幕故障排除工具
Traditional Chinese Subtitle Troubleshooting Tool
"""

import os
import json
from datetime import datetime

def create_troubleshooting_checklist():
    """創建故障排除檢查清單"""
    
    checklist = """
# 🔍 繁體中文字幕故障排除檢查清單

## ✅ 使用前檢查

### 1. Web 介面設置
- [ ] 勾選了 "📝 Enable Subtitles"
- [ ] 勾選了 "🇹🇼 Traditional Chinese Subtitles"
- [ ] 選擇了合適的字幕樣式（建議：Default）

### 2. 瀏覽器檢查
- [ ] 開啟開發者工具 (F12)
- [ ] 切換到 Network 標籤
- [ ] 點擊 "Generate Video" 按鈕
- [ ] 查看 POST 請求到 `/process_with_edited_text`
- [ ] 確認請求包含：`"traditional_chinese": true`

## 🔍 服務器端檢查

### 3. 日誌檢查
在服務器日誌中尋找以下信息：

```
✅ 參數接收確認
🇹🇼 Processing with traditional_chinese=True

✅ 字幕生成器初始化
🇹🇼 Traditional Chinese parameter: True
🏗️ Creating WhisperSubtitleGenerator with traditional_chinese=True
🇹🇼 Traditional Chinese mode: ENABLED

✅ 轉換過程日誌
🔄 Converting Chinese text: 这是简体中文...
🔄 Converted using built-in table: 这是简体中文... → 這是簡體中文...
✅ Conversion result: 這是簡體中文...
```

### 4. 如果沒有看到以上日誌：

#### 參數未正確傳遞
- 檢查瀏覽器 Network 請求數據
- 確認 JavaScript 代碼正確執行
- 重新啟動 Flask 應用程式

#### 字幕功能未啟用
- 確認 `SUBTITLE_AVAILABLE = True`
- 檢查 Whisper 相關依賴安裝

## 🛠️ 常見問題解決

### 問題 1: 參數未傳遞
**症狀**: 日誌顯示 `traditional_chinese=False`
**解決**: 
- 清除瀏覽器快取
- 重新載入頁面
- 確認勾選繁體選項

### 問題 2: 字幕未顯示轉換
**症狀**: 日誌顯示參數正確，但字幕仍為簡體
**解決**:
- 檢查原始文本是否包含中文字符
- 驗證轉換對照表是否包含對應字符
- 查看 SRT 檔案內容確認轉換

### 問題 3: 字體顯示問題
**症狀**: 繁體字符無法正常顯示
**解決**:
- 確保系統安裝繁體中文字體
- 在 Colab 環境中會自動處理字體

### 問題 4: 部分字符未轉換
**症狀**: 只有部分中文字符被轉換
**解決**:
- 這是正常現象，內建轉換表持續更新中
- 可以手動編輯文本調整特定字符
- 考慮安裝 zhconv 庫獲得更完整轉換

## 🧪 調試測試

### 快速測試指令
```bash
# 測試轉換功能
python debug_traditional_chinese.py

# 測試參數傳遞
python debug_web_params.py

# 檢查完整功能
python test_complete_traditional.py
```

## 📞 技術支援

如果以上步驟都無法解決問題，請提供：
1. 瀏覽器 Network 請求截圖
2. 服務器完整日誌
3. 原始文本內容示例
4. 期望的轉換結果

---
生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return checklist

def create_debug_script():
    """創建調試腳本"""
    
    script_content = '''#!/usr/bin/env python3
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
        print("\\n📝 測試簡體模式:")
        gen_simplified = WhisperSubtitleGenerator(traditional_chinese=False)
        print(f"  traditional_chinese 屬性: {gen_simplified.traditional_chinese}")
        
        print("\\n🇹🇼 測試繁體模式:")
        gen_traditional = WhisperSubtitleGenerator(traditional_chinese=True)
        print(f"  traditional_chinese 屬性: {gen_traditional.traditional_chinese}")
        print(f"  use_zhconv 屬性: {getattr(gen_traditional, 'use_zhconv', 'Not found')}")
        
        # 測試轉換功能
        test_texts = [
            "这是简体中文测试",
            "人工智能语音识别技术",
            "Hello world! 这是混合内容。"
        ]
        
        print("\\n🔄 測試文本轉換:")
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
    
    print("\\n🌍 環境檢查")
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
    print(f"\\n📁 Python 路徑:")
    for path in sys.path[:3]:  # 只顯示前3個路徑
        print(f"  - {path}")
    
    # 檢查當前目錄
    print(f"\\n📂 當前目錄: {os.getcwd()}")
    
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
        
        print("\\n" + "=" * 80)
        if test_ok:
            print("✅ 調試完成：繁體轉換功能正常")
            print("\\n💡 如果網頁仍顯示簡體字，請：")
            print("  1. 重新啟動 Flask 應用程式")
            print("  2. 清除瀏覽器快取並重新載入")
            print("  3. 確認勾選繁體中文選項")
            print("  4. 檢查瀏覽器開發者工具的 Network 請求")
        else:
            print("❌ 調試失敗：請檢查環境設置")
    else:
        print("❌ 環境檢查失敗")
'''
    
    return script_content

def main():
    """主函數"""
    
    print("🛠️ 繁體中文字幕故障排除工具")
    print("Traditional Chinese Subtitle Troubleshooting Tool")
    print("=" * 80)
    
    # 創建故障排除檢查清單
    checklist = create_troubleshooting_checklist()
    
    # 保存檢查清單
    checklist_file = "TROUBLESHOOTING_CHECKLIST.md"
    with open(checklist_file, 'w', encoding='utf-8') as f:
        f.write(checklist)
    
    print(f"✅ 故障排除檢查清單已保存: {checklist_file}")
    
    # 創建調試腳本
    debug_script = create_debug_script()
    
    # 保存調試腳本
    debug_file = "debug_realtime.py"
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(debug_script)
    
    print(f"✅ 即時調試腳本已保存: {debug_file}")
    
    print(f"\n📋 使用方法:")
    print(f"  1. 閱讀檢查清單: {checklist_file}")
    print(f"  2. 執行調試腳本: python {debug_file}")
    print(f"  3. 按照檢查清單逐步排除問題")
    
    print(f"\n🎯 常見解決方案:")
    print(f"  • 重新啟動 Flask 應用程式")
    print(f"  • 清除瀏覽器快取")
    print(f"  • 檢查瀏覽器開發者工具 Network 標籤")
    print(f"  • 確認繁體中文選項已勾選")

if __name__ == "__main__":
    main()
