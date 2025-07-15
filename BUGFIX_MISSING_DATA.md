# 🔧 修復 "Missing required data" 錯誤

## 問題描述
在編輯完文字並按下 "Generate Video" 後，系統顯示錯誤：`Error: Missing required data`

## 🔍 根本原因分析

1. **JSON 請求處理錯誤**：
   - 前端使用 `fetch()` 發送 JSON 格式的請求
   - 後端 `process_with_edited_text()` 函數錯誤地嘗試從 `request.files` 和 `request.form` 獲取數據
   - 應該使用 `request.get_json()` 來處理 JSON 請求

2. **會話數據管理**：
   - 檢查 `session['pdf_path']` 和 `session['video_path']` 是否正確設置
   - 確保數據在用戶會話中正確保存

3. **API 函數參數**：
   - `api_with_edited_script()` 函數需要正確的 `poppler_path` 參數
   - 確保所有必需的導入和函數都正確定義

## 🛠️ 修復方案

### 1. 修復 `process_with_edited_text()` 函數
```python
# 修復前（錯誤）：
edited_pages = request.json.get('pages', [])
video_file = request.files.get("video")
resolution = request.form.get("resolution")

# 修復後（正確）：
request_data = request.get_json()
edited_pages = request_data.get('pages', [])
resolution = request_data.get('resolution', 480)
```

### 2. 改進錯誤處理和調試
```python
# 添加詳細的調試信息
app.logger.info(f"Session data - PDF: {pdf_path}, Video: {video_path}, Pages: {len(edited_pages)}")

# 提供更具體的錯誤信息
if not pdf_path or not edited_pages:
    missing_items = []
    if not pdf_path:
        missing_items.append("PDF path")
    if not edited_pages:
        missing_items.append("edited pages")
    return jsonify({
        "status": "error", 
        "message": f"Missing required data: {', '.join(missing_items)}"
    })
```

### 3. 修正 `api_with_edited_script()` 函數
- 使用正確的 PDF 轉圖片方法：`convert_from_path()`
- 添加適當的分辨率驗證
- 改進音頻文件生成和驗證邏輯
- 使用與原始 API 相同的視頻導出參數

### 4. 確保正確的 Poppler 路徑配置
```python
# 添加 POPPLER_PATH 常量
POPPLER_PATH = os.path.join(BASE_DIR, "poppler", "poppler-0.89.0", "bin")
```

## ✅ 修復結果

1. **請求處理**：現在正確處理 JSON 請求
2. **錯誤信息**：提供更詳細的錯誤信息以便調試
3. **會話管理**：確保所有必需的數據都在會話中正確保存
4. **API 兼容性**：`api_with_edited_script()` 函數現在與原始 API 兼容

## 🧪 測試驗證

運行 `debug_two_stage.py` 腳本驗證：
- ✅ 會話數據處理
- ✅ 腳本解析功能
- ✅ JSON 請求處理

## 📋 使用流程

1. 用戶上傳 PDF 文件
2. 系統生成文本（第一階段）
3. 用戶編輯文本
4. 系統處理編輯後的文本並生成視頻（第二階段）

現在系統應該能夠正確處理編輯後的文本並生成視頻，不再出現 "Missing required data" 錯誤。
