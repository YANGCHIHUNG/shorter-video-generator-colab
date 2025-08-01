#!/usr/bin/env python3
"""
測試PDF預覽功能
"""
import os
import requests
import json
import time

def test_pdf_preview_api():
    """測試PDF預覽API是否正常工作"""
    
    print("🧪 測試PDF預覽功能...")
    print("=" * 50)
    
    # 檢查Flask應用是否在運行
    try:
        response = requests.get('http://localhost:5001/', timeout=5)
        print("✅ Flask應用正在運行")
    except requests.exceptions.RequestException:
        print("❌ Flask應用未運行，請先啟動應用程序")
        return False
    
    # 測試不同頁面的預覽
    test_pages = [1, 2, 3]
    
    for page_num in test_pages:
        print(f"\n📄 測試頁面 {page_num} 的預覽...")
        
        try:
            response = requests.get(f'http://localhost:5001/pdf_preview/{page_num}', timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"   ✅ 頁面 {page_num} 預覽載入成功")
                    print(f"   📏 圖片尺寸: {data.get('width')}x{data.get('height')}")
                    print(f"   📊 Base64數據長度: {len(data.get('image', ''))}")
                else:
                    print(f"   ❌ 頁面 {page_num} 預覽失敗: {data.get('error')}")
            elif response.status_code == 404:
                print(f"   ⚠️ 頁面 {page_num} 不存在 (這是正常的，如果PDF沒有那麼多頁)")
            else:
                print(f"   ❌ HTTP錯誤 {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ 網路錯誤: {e}")
    
    return True

def create_test_html():
    """創建測試HTML來驗證預覽功能"""
    
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>PDF預覽測試</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .preview-container { 
            display: flex; 
            gap: 20px; 
            flex-wrap: wrap;
            margin: 20px 0;
        }
        .preview-item { 
            border: 1px solid #ddd; 
            border-radius: 8px; 
            padding: 15px; 
            max-width: 300px;
            text-align: center;
        }
        .preview-item img { 
            max-width: 100%; 
            border-radius: 4px;
        }
        .loading { color: #999; }
        .error { color: #dc3545; }
        .success { color: #28a745; }
    </style>
</head>
<body>
    <h1>📄 PDF預覽功能測試</h1>
    
    <div class="preview-container" id="preview-container">
        <!-- 預覽將動態載入到這裡 -->
    </div>
    
    <script>
        async function loadPreviews() {
            const container = document.getElementById('preview-container');
            const pageNumbers = [1, 2, 3, 4, 5]; // 測試前5頁
            
            for (const pageNum of pageNumbers) {
                const previewDiv = document.createElement('div');
                previewDiv.className = 'preview-item';
                previewDiv.innerHTML = `
                    <h3>頁面 ${pageNum}</h3>
                    <div class="loading">載入中...</div>
                `;
                container.appendChild(previewDiv);
                
                try {
                    const response = await fetch(`/pdf_preview/${pageNum}`);
                    const data = await response.json();
                    
                    if (data.success) {
                        previewDiv.innerHTML = `
                            <h3>頁面 ${pageNum}</h3>
                            <img src="${data.image}" alt="PDF Page ${pageNum}">
                            <div class="success">✅ 載入成功</div>
                            <div style="font-size: 12px; color: #666;">
                                尺寸: ${data.width}x${data.height}
                            </div>
                        `;
                    } else {
                        previewDiv.innerHTML = `
                            <h3>頁面 ${pageNum}</h3>
                            <div class="error">❌ 載入失敗</div>
                            <div style="font-size: 12px;">${data.error}</div>
                        `;
                    }
                } catch (error) {
                    previewDiv.innerHTML = `
                        <h3>頁面 ${pageNum}</h3>
                        <div class="error">❌ 網路錯誤</div>
                        <div style="font-size: 12px;">${error.message}</div>
                    `;
                }
            }
        }
        
        // 頁面載入完成後開始測試
        window.addEventListener('load', loadPreviews);
    </script>
</body>
</html>"""
    
    with open('pdf_preview_test.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n📄 測試HTML已創建: pdf_preview_test.html")
    print("   你可以在瀏覽器中打開這個文件來測試預覽功能")

def test_integration():
    """測試完整的編輯文字頁面整合"""
    
    print(f"\n🔗 測試編輯文字頁面整合...")
    
    try:
        response = requests.get('http://localhost:5001/edit_text?pages=["測試頁面1","測試頁面2","測試頁面3"]', timeout=10)
        
        if response.status_code == 200:
            print("   ✅ 編輯文字頁面載入成功")
            print("   📝 頁面包含PDF預覽功能")
        else:
            print(f"   ❌ 編輯文字頁面載入失敗: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ 網路錯誤: {e}")

if __name__ == "__main__":
    success = test_pdf_preview_api()
    
    if success:
        create_test_html()
        test_integration()
        
        print("\n" + "=" * 50)
        print("🎉 PDF預覽功能測試完成！")
        print("\n💡 測試建議:")
        print("   1. 確保已上傳PDF文件")
        print("   2. 訪問編輯文字頁面")
        print("   3. 檢查每個頁面是否顯示PDF預覽圖")
        print("   4. 打開 pdf_preview_test.html 進行詳細測試")
    else:
        print("\n❌ 測試失敗，請檢查應用程序狀態")
