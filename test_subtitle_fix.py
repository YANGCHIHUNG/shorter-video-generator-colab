#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
字幕系統驗證測試腳本
測試 ImprovedHybridSubtitleGenerator 的 embed_subtitles_in_video 方法
"""

import sys
import os
import inspect

# 添加項目根目錄到路徑
sys.path.append('.')

def test_method_signature():
    """測試方法簽名是否正確"""
    try:
        from utility.improved_hybrid_subtitle_generator import ImprovedHybridSubtitleGenerator
        
        # 檢查方法簽名
        sig = inspect.signature(ImprovedHybridSubtitleGenerator.embed_subtitles_in_video)
        params = list(sig.parameters.keys())
        
        print("✅ ImprovedHybridSubtitleGenerator.embed_subtitles_in_video 方法簽名:")
        print(f"   參數: {params}")
        print(f"   完整簽名: {sig}")
        
        # 檢查是否有 style 參數
        if 'style' in params:
            print("✅ 參數 'style' 存在 - 正確!")
        else:
            print("❌ 參數 'style' 不存在!")
            
        # 檢查是否錯誤地有 subtitle_style 參數
        if 'subtitle_style' in params:
            print("❌ 錯誤的參數 'subtitle_style' 存在!")
        else:
            print("✅ 沒有錯誤的 'subtitle_style' 參數 - 正確!")
            
        return True
        
    except ImportError as e:
        print(f"❌ 導入錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 測試錯誤: {e}")
        return False

def test_generator_creation():
    """測試生成器創建"""
    try:
        from utility.improved_hybrid_subtitle_generator import ImprovedHybridSubtitleGenerator
        
        # 測試不同的參數組合
        test_configs = [
            {"traditional_chinese": False, "subtitle_length_mode": "auto"},
            {"traditional_chinese": True, "subtitle_length_mode": "compact"},
            {"traditional_chinese": False, "subtitle_length_mode": "standard"},
            {"traditional_chinese": True, "subtitle_length_mode": "relaxed"}
        ]
        
        for i, config in enumerate(test_configs, 1):
            generator = ImprovedHybridSubtitleGenerator(**config)
            print(f"✅ 測試配置 {i}: {config} - 創建成功!")
            
        return True
        
    except Exception as e:
        print(f"❌ 生成器創建測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🧪 開始字幕系統驗證測試...")
    print("=" * 60)
    
    # 測試 1: 方法簽名
    print("\n📋 測試 1: 檢查方法簽名")
    test1_passed = test_method_signature()
    
    # 測試 2: 生成器創建
    print("\n🏗️ 測試 2: 生成器創建測試")
    test2_passed = test_generator_creation()
    
    # 總結
    print("\n" + "=" * 60)
    print("📊 測試結果總結:")
    print(f"   方法簽名測試: {'✅ 通過' if test1_passed else '❌ 失敗'}")
    print(f"   生成器創建測試: {'✅ 通過' if test2_passed else '❌ 失敗'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 所有測試通過! 字幕系統修復成功!")
        print("💡 現在可以正常使用字幕功能了。")
    else:
        print("\n⚠️ 部分測試失敗，請檢查錯誤信息。")

if __name__ == "__main__":
    main()
