#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前端字幕方法選擇功能測試
Test frontend subtitle method selection functionality
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_frontend_integration():
    """測試前端集成是否正確"""
    
    # 檢查前端模板文件是否包含新的字幕方法選擇
    template_path = "templates/edit_text.html"
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查關鍵元素是否存在
        checks = [
            ('subtitle_method選擇框', 'name="subtitle_method"' in content),
            ('語速計算選項', 'value="speech_rate"' in content),
            ('Whisper映射選項', 'value="whisper"' in content),
            ('JavaScript事件處理', 'subtitle_method' in content and 'addEventListener' in content),
            ('表單提交包含新參數', 'subtitle_method:' in content),
        ]
        
        logger.info("🔍 前端模板文件檢查結果：")
        all_passed = True
        
        for check_name, result in checks:
            status = "✅ 通過" if result else "❌ 失敗"
            logger.info(f"  {check_name}: {status}")
            if not result:
                all_passed = False
        
        return all_passed
        
    except FileNotFoundError:
        logger.error(f"❌ 模板文件不存在: {template_path}")
        return False
    except Exception as e:
        logger.error(f"❌ 讀取模板文件失敗: {e}")
        return False

def test_backend_integration():
    """測試後端集成是否正確"""
    
    # 檢查 app.py 是否正確處理新參數
    app_path = "app.py"
    
    try:
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查關鍵代碼是否存在
        checks = [
            ('接收subtitle_method參數', 'subtitle_method = request_data.get' in content),
            ('傳遞到API調用', 'subtitle_method=subtitle_method' in content),
            ('預設值設定', "'speech_rate'" in content),
        ]
        
        logger.info("🔍 後端應用文件檢查結果：")
        all_passed = True
        
        for check_name, result in checks:
            status = "✅ 通過" if result else "❌ 失敗"
            logger.info(f"  {check_name}: {status}")
            if not result:
                all_passed = False
        
        return all_passed
        
    except FileNotFoundError:
        logger.error(f"❌ 應用文件不存在: {app_path}")
        return False
    except Exception as e:
        logger.error(f"❌ 讀取應用文件失敗: {e}")
        return False

def test_api_integration():
    """測試API集成是否正確"""
    
    # 檢查 API 文件是否支援新參數
    api_path = "api/whisper_LLM_api.py"
    
    try:
        with open(api_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查關鍵代碼是否存在
        checks = [
            ('API函數參數', 'subtitle_method=' in content),
            ('條件判斷邏輯', 'if subtitle_method ==' in content),
            ('語速計算調用', 'generate_subtitles_by_speech_rate' in content),
            ('Whisper映射調用', 'generate_hybrid_subtitles' in content),
        ]
        
        logger.info("🔍 API文件檢查結果：")
        all_passed = True
        
        for check_name, result in checks:
            status = "✅ 通過" if result else "❌ 失敗"
            logger.info(f"  {check_name}: {status}")
            if not result:
                all_passed = False
        
        return all_passed
        
    except FileNotFoundError:
        logger.error(f"❌ API文件不存在: {api_path}")
        return False
    except Exception as e:
        logger.error(f"❌ 讀取API文件失敗: {e}")
        return False

def main():
    """主測試函數"""
    logger.info("🚀 開始測試前端字幕方法選擇功能")
    
    # 執行各項測試
    logger.info("\n" + "="*50)
    logger.info("測試 1: 前端模板集成")
    logger.info("="*50)
    frontend_ok = test_frontend_integration()
    
    logger.info("\n" + "="*50)
    logger.info("測試 2: 後端應用集成")
    logger.info("="*50)
    backend_ok = test_backend_integration()
    
    logger.info("\n" + "="*50)
    logger.info("測試 3: API集成")
    logger.info("="*50)
    api_ok = test_api_integration()
    
    # 測試總結
    logger.info("\n" + "="*50)
    logger.info("測試總結")
    logger.info("="*50)
    
    logger.info(f"前端模板集成: {'✅ 通過' if frontend_ok else '❌ 失敗'}")
    logger.info(f"後端應用集成: {'✅ 通過' if backend_ok else '❌ 失敗'}")
    logger.info(f"API集成: {'✅ 通過' if api_ok else '❌ 失敗'}")
    
    if frontend_ok and backend_ok and api_ok:
        logger.info("🎉 所有測試通過！字幕方法選擇功能已成功集成")
        logger.info("\n📋 用戶現在可以在前端選擇字幕生成方法：")
        logger.info("  • 語速計算（推薦）- 適合已知完整文稿")
        logger.info("  • Whisper映射 - 適合語音內容未知")
    else:
        logger.error("⚠️ 部分測試失敗，請檢查相關文件")
    
    return frontend_ok and backend_ok and api_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
