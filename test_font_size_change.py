#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試字幕字體大小修改
Test subtitle font size modification
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_font_size_change():
    """測試字體大小是否已修改"""
    
    try:
        # 讀取 improved_hybrid_subtitle_generator.py 檔案
        with open('utility/improved_hybrid_subtitle_generator.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查字體大小修改
        checks = [
            ('FontSize=18 在完整樣式中', 'FontSize=18,PrimaryColour=&Hffffff,SecondaryColour=&Hffffff' in content),
            ('FontSize=18 在簡化樣式中', 'FontSize=18,PrimaryColour=&Hffffff,OutlineColour=&H0' in content),
            ('沒有遺留的 FontSize=24', 'FontSize=24' not in content),
        ]
        
        logger.info("🔍 字體大小修改檢查：")
        all_passed = True
        
        for check_name, result in checks:
            status = "✅ 通過" if result else "❌ 失敗"
            logger.info(f"  {check_name}: {status}")
            if not result:
                all_passed = False
        
        # 計算當前字體大小
        import re
        font_sizes = re.findall(r'FontSize=(\d+)', content)
        if font_sizes:
            logger.info(f"📊 發現的字體大小: {set(font_sizes)}")
        
        return all_passed
        
    except Exception as e:
        logger.error(f"❌ 檢查字體大小失敗: {e}")
        return False

def test_subtitle_generator_import():
    """測試字幕生成器能否正常導入"""
    
    try:
        # 嘗試導入字幕生成器
        from utility.improved_hybrid_subtitle_generator import ImprovedHybridSubtitleGenerator
        logger.info("✅ ImprovedHybridSubtitleGenerator 導入成功")
        
        # 創建實例測試
        generator = ImprovedHybridSubtitleGenerator(traditional_chinese=False)
        logger.info("✅ 字幕生成器實例創建成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 字幕生成器導入失敗: {e}")
        return False

def test_font_size_comparison():
    """顯示字體大小變化的對比"""
    
    logger.info("📋 字體大小變化對比：")
    logger.info("  修改前: FontSize=24")
    logger.info("  修改後: FontSize=18")
    logger.info("  縮小比例: 25% (18/24 = 0.75)")
    
    logger.info("\n🎯 預期效果：")
    logger.info("  • 字幕字體變小，更不會遮擋視頻內容")
    logger.info("  • 適合在小螢幕或手機上觀看")
    logger.info("  • 保持清晰度的同時減少干擾")
    
    return True

def main():
    """主測試函數"""
    logger.info("🚀 開始測試字幕字體大小修改")
    
    # 執行各項測試
    logger.info("\n" + "="*50)
    logger.info("測試 1: 字體大小修改檢查")
    logger.info("="*50)
    size_ok = test_font_size_change()
    
    logger.info("\n" + "="*50)
    logger.info("測試 2: 字幕生成器導入測試")
    logger.info("="*50)
    import_ok = test_subtitle_generator_import()
    
    logger.info("\n" + "="*50)
    logger.info("測試 3: 字體大小變化對比")
    logger.info("="*50)
    comparison_ok = test_font_size_comparison()
    
    # 測試總結
    logger.info("\n" + "="*50)
    logger.info("字體大小修改總結")
    logger.info("="*50)
    
    logger.info(f"字體大小修改檢查: {'✅ 通過' if size_ok else '❌ 失敗'}")
    logger.info(f"字幕生成器導入測試: {'✅ 通過' if import_ok else '❌ 失敗'}")
    logger.info(f"字體大小變化對比: {'✅ 完成' if comparison_ok else '❌ 失敗'}")
    
    if size_ok and import_ok:
        logger.info("🎉 字體大小修改成功！")
        logger.info("\n📝 修改詳情：")
        logger.info("  • 完整樣式字體大小: 24 → 18")
        logger.info("  • 簡化樣式字體大小: 24 → 18")
        logger.info("  • 字體縮小比例: 25%")
        logger.info("  • 所有字幕樣式都會使用較小字體")
    else:
        logger.error("⚠️ 字體大小修改可能有問題，請檢查")
    
    return size_ok and import_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
