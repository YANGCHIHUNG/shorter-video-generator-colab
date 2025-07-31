#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔍 檢查 OpenCC 安裝和可用性
"""

def check_opencc():
    print("🔍 檢查 OpenCC 安裝狀態")
    print("=" * 50)
    
    # 檢查 OpenCC 是否安裝
    try:
        import opencc
        print("✅ OpenCC 已安裝")
        print(f"   版本: {opencc.__version__ if hasattr(opencc, '__version__') else '未知'}")
        
        # 測試初始化
        try:
            converter = opencc.OpenCC('s2t')
            print("✅ OpenCC 初始化成功")
            
            # 測試轉換
            test_text = "这是一个测试文本，包含简体中文字符。"
            result = converter.convert(test_text)
            print(f"✅ 轉換測試成功:")
            print(f"   原文: {test_text}")
            print(f"   轉換: {result}")
            
        except Exception as e:
            print(f"❌ OpenCC 初始化失敗: {e}")
            
    except ImportError as e:
        print(f"❌ OpenCC 未安裝或導入失敗: {e}")
    
    # 檢查 zhconv
    print("\n🔍 檢查 zhconv 狀態")
    try:
        import zhconv
        print("✅ zhconv 已安裝")
        test_text = "这是一个测试文本"
        result = zhconv.convert(test_text, 'zh-tw')
        print(f"✅ zhconv 轉換測試: {test_text} → {result}")
    except ImportError:
        print("❌ zhconv 未安裝")

    # 檢查環境變數
    print("\n🔍 檢查環境狀態")
    import sys
    print(f"Python 版本: {sys.version}")
    print(f"Python 路徑: {sys.executable}")

if __name__ == "__main__":
    check_opencc()
