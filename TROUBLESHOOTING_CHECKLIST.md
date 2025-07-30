
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
