#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 subtitle_method 參數錯誤修復
Test subtitle_method parameter error fix
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_function_signature():
    """測試函數簽名是否正確"""
    
    try:
        # 讀取 app.py 檔案
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查關鍵修復
        checks = [
            ('run_processing_with_edited_text 函數參數', 'subtitle_method="speech_rate"' in content),
            ('線程調用傳遞參數', 'args=(video_path, pdf_path, edited_pages, resolution, user_folder, TTS_model_type, voice, enable_subtitles, subtitle_method, subtitle_style, traditional_chinese, subtitle_length_mode)' in content),
            ('API 調用傳遞參數', 'subtitle_method=subtitle_method,' in content),
            ('調試信息包含字幕方法', '字幕方法: {subtitle_method}' in content),
            ('process_with_edited_text 獲取參數', 'subtitle_method = request_data.get' in content),
        ]
        
        logger.info("🔍 函數簽名和參數傳遞檢查：")
        all_passed = True
        
        for check_name, result in checks:
            status = "✅ 通過" if result else "❌ 失敗"
            logger.info(f"  {check_name}: {status}")
            if not result:
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        logger.error(f"❌ 檢查函數簽名失敗: {e}")
        return False

def test_import_app():
    """測試能否正常導入 app 模組"""
    
    try:
        # 嘗試導入 app 模組
        import app
        logger.info("✅ app 模組導入成功")
        
        # 檢查 run_processing_with_edited_text 函數是否存在
        if hasattr(app, 'run_processing_with_edited_text'):
            logger.info("✅ run_processing_with_edited_text 函數存在")
            
            # 檢查函數簽名（通過檢查函數的參數名稱）
            import inspect
            sig = inspect.signature(app.run_processing_with_edited_text)
            params = list(sig.parameters.keys())
            
            if 'subtitle_method' in params:
                logger.info("✅ subtitle_method 參數已添加到函數簽名中")
                
                # 檢查預設值
                param = sig.parameters['subtitle_method']
                if param.default == 'speech_rate':
                    logger.info("✅ subtitle_method 預設值正確設為 'speech_rate'")
                    return True
                else:
                    logger.error(f"❌ subtitle_method 預設值錯誤: {param.default}")
                    return False
            else:
                logger.error("❌ subtitle_method 參數未添加到函數簽名中")
                return False
        else:
            logger.error("❌ run_processing_with_edited_text 函數不存在")
            return False
            
    except Exception as e:
        logger.error(f"❌ 導入測試失敗: {e}")
        return False

def test_api_function():
    """測試 API 函數簽名"""
    
    try:
        from api.whisper_LLM_api import api_with_edited_script
        import inspect
        
        sig = inspect.signature(api_with_edited_script)
        params = list(sig.parameters.keys())
        
        if 'subtitle_method' in params:
            param = sig.parameters['subtitle_method']
            logger.info(f"✅ API 函數包含 subtitle_method 參數，預設值: {param.default}")
            return True
        else:
            logger.error("❌ API 函數缺少 subtitle_method 參數")
            return False
            
    except Exception as e:
        logger.error(f"❌ API 函數測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    logger.info("🚀 開始測試 subtitle_method 參數錯誤修復")
    
    # 執行各項測試
    logger.info("\n" + "="*50)
    logger.info("測試 1: 函數簽名和參數傳遞")
    logger.info("="*50)
    signature_ok = test_function_signature()
    
    logger.info("\n" + "="*50)
    logger.info("測試 2: 模組導入和函數檢查")
    logger.info("="*50)
    import_ok = test_import_app()
    
    logger.info("\n" + "="*50)
    logger.info("測試 3: API 函數檢查")
    logger.info("="*50)
    api_ok = test_api_function()
    
    # 測試總結
    logger.info("\n" + "="*50)
    logger.info("修復驗證總結")
    logger.info("="*50)
    
    logger.info(f"函數簽名和參數傳遞: {'✅ 通過' if signature_ok else '❌ 失敗'}")
    logger.info(f"模組導入和函數檢查: {'✅ 通過' if import_ok else '❌ 失敗'}")
    logger.info(f"API 函數檢查: {'✅ 通過' if api_ok else '❌ 失敗'}")
    
    if signature_ok and import_ok and api_ok:
        logger.info("🎉 所有測試通過！subtitle_method 參數錯誤已修復")
        logger.info("\n📋 修復內容：")
        logger.info("  • run_processing_with_edited_text 函數增加 subtitle_method 參數")
        logger.info("  • 線程調用時正確傳遞 subtitle_method 參數") 
        logger.info("  • 添加調試信息顯示字幕方法選擇")
        logger.info("  • 設定預設值為 'speech_rate'")
    else:
        logger.error("⚠️ 部分測試失敗，請檢查修復內容")
    
    return signature_ok and import_ok and api_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
