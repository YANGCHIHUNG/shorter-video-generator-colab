# 🔧 修復 "Missing required data: PDF path" 錯誤

## 問題分析

當用戶編輯完文字並按下 "Generate Video" 後，系統顯示錯誤：`Error: Missing required data: PDF path`

## 🔍 根本原因

1. **Flask 會話持久性問題**：
   - 在兩階段處理中，第一階段（`generate_text`）將 PDF 路徑存儲在 Flask session 中
   - 第二階段（`process_with_edited_text`）嘗試從 session 中讀取 PDF 路徑
   - 由於 Flask 會話配置或瀏覽器會話管理問題，數據可能丟失

2. **Poppler 配置更改**：
   - 用戶從使用下載的 poppler 資料夾改為使用系統安裝的 Poppler 套件
   - 需要將 `poppler_path` 設為 `None` 以使用系統安裝的版本

## 🛠️ 解決方案

### 1. 改善 Flask 會話配置
```python
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
```

### 2. 實施會話備份機制
創建了一個備份系統，將關鍵會話數據同時存儲在：
- Flask session（主要）
- 文件系統備份（`session_backup.json`）

核心函數：
- `save_session_backup()`: 保存會話數據到文件
- `load_session_backup()`: 從文件讀取會話數據
- `get_session_data()`: 優先從 session 讀取，失敗時從備份讀取
- `set_session_data()`: 同時設置 session 和備份

### 3. 更新 Poppler 配置
將所有 `poppler_path` 參數設為 `None`，使用系統安裝的 Poppler：
```python
poppler_path=None  # Use system-installed Poppler
```

### 4. 增強調試信息
添加詳細的日誌記錄：
- 會話數據保存時的記錄
- 會話數據讀取時的記錄
- 錯誤情況的具體信息

## 📋 修改的文件

### `app.py` 主要修改：

1. **Flask 配置**：
   - 添加會話配置參數
   - 導入 JSON 處理模塊

2. **會話備份系統**：
   - 新增 4 個會話管理函數
   - 實現文件備份機制

3. **`generate_text` 函數**：
   - 使用 `set_session_data()` 保存會話數據
   - 設置 `poppler_path=None`
   - 增加調試日誌

4. **`process_with_edited_text` 函數**：
   - 使用 `get_session_data()` 讀取會話數據
   - 增強錯誤處理和調試信息

5. **`run_processing_with_edited_text` 函數**：
   - 設置 `poppler_path=None`

6. **`edit_text` 路由**：
   - 使用新的會話管理機制
   - 改善會話數據驗證

## 🎯 解決的問題

1. **會話持久性**：通過備份機制確保數據不會丟失
2. **Poppler 兼容性**：正確使用系統安裝的 Poppler
3. **錯誤診斷**：提供詳細的錯誤信息和調試日誌
4. **系統穩定性**：雙重存儲確保數據可靠性

## 🔄 工作流程

1. **第一階段**（`generate_text`）：
   - 處理 PDF 和視頻文件
   - 生成文本內容
   - 使用 `set_session_data()` 保存到 session 和備份

2. **第二階段**（`process_with_edited_text`）：
   - 使用 `get_session_data()` 讀取數據
   - 如果 session 中沒有，自動從備份讀取
   - 處理編輯後的文本生成視頻

## 🧪 測試驗證

創建了調試腳本來驗證：
- 會話數據持久性
- 會話鍵值處理
- Poppler 配置

## 📝 使用說明

現在系統應該能夠：
1. 正確保存和讀取會話數據
2. 使用系統安裝的 Poppler 處理 PDF
3. 在會話失效時自動恢復數據
4. 提供詳細的錯誤診斷信息

如果仍然遇到問題，請檢查：
1. 系統是否正確安裝了 Poppler
2. 用戶輸出文件夾的寫入權限
3. Flask 應用的日誌輸出以獲得更多信息
