#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧪 驗證繁體中文預設啟用修改
測試確認：
1. edit_text.html 中已移除繁體中文選項框
2. JavaScript 始終將 traditional_chinese 設為 true
"""

import os
import re

def verify_edit_text_modifications():
    print("🔍 驗證 edit_text.html 修改")
    print("=" * 50)
    
    edit_text_path = "templates/edit_text.html"
    
    if not os.path.exists(edit_text_path):
        print("❌ edit_text.html 文件不存在")
        return False
    
    with open(edit_text_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查1: 確認已移除繁體中文選項框
    checkbox_patterns = [
        r'name="traditional_chinese"',
        r'id="traditional_chinese"',
        r'Traditional Chinese Subtitles',
        r'Convert simplified Chinese subtitles to traditional Chinese'
    ]
    
    print("📋 檢查1: 確認已移除繁體中文選項框")
    checkbox_removed = True
    for pattern in checkbox_patterns:
        if re.search(pattern, content):
            print(f"  ❌ 仍然找到: {pattern}")
            checkbox_removed = False
        else:
            print(f"  ✅ 已移除: {pattern}")
    
    if checkbox_removed:
        print("  ✅ 繁體中文選項框已完全移除")
    else:
        print("  ❌ 繁體中文選項框仍然存在")
    
    print()
    
    # 檢查2: 確認 JavaScript 設定為 true
    print("📋 檢查2: 確認 JavaScript 中 traditional_chinese 設為 true")
    
    # 尋找 traditional_chinese 的設定
    traditional_chinese_pattern = r'traditional_chinese:\s*([^,}]+)'
    matches = re.findall(traditional_chinese_pattern, content)
    
    if matches:
        for i, match in enumerate(matches, 1):
            match = match.strip()
            print(f"  找到設定 {i}: traditional_chinese: {match}")
            if match == 'true':
                print(f"  ✅ 設定 {i} 正確: 已設為 true")
            else:
                print(f"  ❌ 設定 {i} 錯誤: 應為 true，實際為 {match}")
    else:
        print("  ❌ 未找到 traditional_chinese 設定")
        return False
    
    print()
    
    # 檢查3: 確認有註解說明
    print("📋 檢查3: 確認有適當的註解說明")
    comment_patterns = [
        r'Traditional Chinese conversion is now enabled by default',
        r'Checkbox removed as requested',
        r'Always enable traditional Chinese conversion'
    ]
    
    comments_found = 0
    for pattern in comment_patterns:
        if re.search(pattern, content):
            print(f"  ✅ 找到註解: {pattern}")
            comments_found += 1
        else:
            print(f"  ⚠️ 未找到註解: {pattern}")
    
    if comments_found >= 2:
        print("  ✅ 註解說明充足")
    else:
        print("  ⚠️ 註解說明不足")
    
    print()
    print("🎯 總結:")
    if checkbox_removed and matches and any(m.strip() == 'true' for m in matches):
        print("✅ 修改成功！繁體中文轉換已設為預設啟用")
        print("📝 效果:")
        print("  - 用戶無法看到繁體中文選項框")
        print("  - 系統自動將所有簡體中文轉換為繁體中文")
        print("  - 無需用戶手動勾選")
        return True
    else:
        print("❌ 修改不完整，請檢查上述問題")
        return False

if __name__ == "__main__":
    verify_edit_text_modifications()
