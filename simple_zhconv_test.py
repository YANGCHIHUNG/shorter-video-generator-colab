#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
簡單的 zhconv 測試
"""

def test_zhconv():
    try:
        import zhconv
        print("✅ zhconv 導入成功")
        
        test_text = "这是一个测试文本"
        result = zhconv.convert(test_text, 'zh-tw')
        
        print(f"原文: {test_text}")
        print(f"轉換: {result}")
        
        return True
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

if __name__ == "__main__":
    test_zhconv()
