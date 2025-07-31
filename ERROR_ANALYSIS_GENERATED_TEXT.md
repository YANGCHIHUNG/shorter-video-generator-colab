# "Error loading generated text. Please try again." 錯誤分析

## 🚨 錯誤出現條件

根據代碼分析，"Error loading generated text. Please try again." 這個錯誤會在以下情況下出現：

### 1. **URL 參數解析錯誤** 📍
當用戶通過 URL 參數傳遞頁面數據時，如果數據格式不正確：

```javascript
// edit_text.html 第 103-113 行
const pages = urlParams.get('pages');
if (pages) {
    try {
        currentPages = JSON.parse(decodeURIComponent(pages));
        originalPages = [...currentPages];
        renderPages();
    } catch (e) {
        console.error('Error parsing pages:', e);
        alert('Error loading generated text. Please try again.');  // ← 這裡！
        window.location.href = '/';
    }
}
```

**觸發條件：**
- URL 中的 `pages` 參數包含無效的 JSON 格式
- 參數被損壞或不完整
- 編碼/解碼過程中出現問題

### 2. **缺少生成文本數據** 📄
當既沒有 URL 參數，後端也沒有提供有效的頁面數據：

```javascript
// edit_text.html 第 114-125 行
} else {
    // Try to get pages from backend
    const backendPages = {{ pages_json|default('null')|safe }};
    if (backendPages && backendPages.length > 0) {
        currentPages = backendPages;
        originalPages = [...currentPages];
        renderPages();
    } else {
        alert('No generated text found. Please start from the upload page.');  // ← 類似錯誤
        window.location.href = '/';
    }
}
```

**注意：** 這裡顯示的是稍微不同的錯誤訊息，但邏輯相同。

## 🔍 具體場景分析

### 場景 1：直接訪問編輯頁面
```
用戶直接訪問：http://localhost:5000/edit_text
結果：顯示 "No generated text found. Please start from the upload page."
```

### 場景 2：損壞的 URL 參數
```
錯誤的 URL：http://localhost:5000/edit_text?pages=invalid_json
結果：顯示 "Error loading generated text. Please try again."
```

### 場景 3：截斷的 JSON 數據
```
不完整的 URL：http://localhost:5000/edit_text?pages=%5B%22page1%22%2C%22pa
結果：顯示 "Error loading generated text. Please try again."
```

### 場景 4：Session 數據丟失
```
用戶刷新頁面但 session 已過期或清除
結果：顯示 "No generated text found. Please start from the upload page."
```

## 🛠️ 後端相關代碼

在 `app.py` 的 `edit_text()` 函數中：

```python
@app.route('/edit_text')
def edit_text():
    # 檢查 URL 參數
    pages_param = request.args.get('pages')
    
    generated_pages = []
    if pages_param:
        try:
            generated_pages = json.loads(pages_param)  # 可能失敗
        except (json.JSONDecodeError, TypeError) as e:
            app.logger.error(f"Error parsing pages parameter: {e}")
    
    # 從 session 獲取數據
    if not generated_pages:
        generated_pages = get_session_data('generated_pages', [])
    
    # 如果還是沒有數據
    if not generated_pages:
        flash('No generated text found. Please start from the upload page.', 'error')
        return redirect(url_for('index'))
```

## 🐛 問題根源

### 主要原因：
1. **前端模板錯誤**: `pages_json` 變量未在後端定義，導致前端接收到 `null`
2. **數據流失**: URL 參數或 session 數據在傳輸過程中丟失或損壞
3. **編碼問題**: JSON 數據在 URL 編碼/解碼過程中出現問題

### 修復建議：

#### 1. 修復後端模板變量
```python
# 在 app.py 的 edit_text() 函數中
return render_template('edit_text.html', 
                      pages=generated_pages,
                      pages_json=json.dumps(generated_pages),  # ← 添加這行
                      TTS_model_type=TTS_model_type,
                      resolution=resolution,
                      voice=voice)
```

#### 2. 增強前端錯誤處理
```javascript
// 更好的錯誤處理
try {
    currentPages = JSON.parse(decodeURIComponent(pages));
    if (!Array.isArray(currentPages) || currentPages.length === 0) {
        throw new Error('Invalid pages data format');
    }
} catch (e) {
    console.error('Error parsing pages:', e);
    // 嘗試從 session 恢復數據而不是直接跳轉
    location.reload();
}
```

#### 3. 添加數據驗證
```python
# 在後端添加數據驗證
def validate_pages_data(pages_data):
    if not pages_data:
        return False
    if not isinstance(pages_data, list):
        return False
    if len(pages_data) == 0:
        return False
    return all(isinstance(page, str) for page in pages_data)
```

## 📋 快速診斷檢查表

當用戶遇到此錯誤時，檢查以下項目：

- [ ] 用戶是否從正常流程進入編輯頁面？
- [ ] URL 參數是否完整且格式正確？
- [ ] Session 數據是否存在？
- [ ] 瀏覽器是否禁用了 JavaScript？
- [ ] 網絡連接是否穩定？
- [ ] 是否有特殊字符導致編碼問題？

## 🔧 臨時解決方案

如果用戶遇到此錯誤，可以：

1. **重新開始流程**: 返回首頁重新上傳文件
2. **清除瀏覽器緩存**: 清除 cookies 和 session 數據
3. **檢查 URL**: 確保 URL 參數完整無損
4. **重新生成**: 重新執行文本生成過程

---

這個錯誤主要是由於數據傳輸過程中的問題導致的，通過改善錯誤處理和數據驗證可以大大減少發生頻率。
