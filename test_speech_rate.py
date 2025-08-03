#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Speech Rate Subtitle Generation Test
Tests the new speech rate calculation method for subtitle generation
"""

import os
import sys
import logging

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utility.improved_hybrid_subtitle_generator import ImprovedHybridSubtitleGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_speech_rate_calculation():
    """Test the speech rate calculation method"""
    try:
        # Initialize the subtitle generator
        generator = ImprovedHybridSubtitleGenerator(traditional_chinese=False)
        
        # Test text samples (simulate typical Chinese content)
        test_texts = [
            "大家好，歡迎觀看今天的影片。今天我們將討論人工智慧的發展趨勢。",
            "機器學習是人工智慧的一個重要分支，它能夠讓電腦從資料中學習。",
            "深度學習使用神經網絡來模擬人腦的運作方式，在圖像識別和自然語言處理方面表現出色。"
        ]
        
        # Test speech rate calculation
        logger.info("🧪 Testing speech rate calculation...")
        
        # Test individual components
        logger.info("📊 Testing character counting...")
        for i, text in enumerate(test_texts):
            effective_chars = generator._count_effective_characters(text)
            logger.info(f"Text {i+1}: {len(text)} total chars, {effective_chars} effective chars")
            logger.info(f"Content: {text[:50]}...")
        
        # Test punctuation pause calculation
        logger.info("⏱️ Testing pause time calculation...")
        combined_text = "。".join(test_texts) + "。"
        pause_time = generator._calculate_pause_time(combined_text)
        logger.info(f"Combined text pause time: {pause_time:.2f} seconds")
        
        logger.info("✅ Speech rate calculation components test completed!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_speech_rate_method_availability():
    """Test if the speech rate method is available"""
    try:
        generator = ImprovedHybridSubtitleGenerator(traditional_chinese=False)
        
        # Check if method exists
        if hasattr(generator, 'generate_subtitles_by_speech_rate'):
            logger.info("✅ generate_subtitles_by_speech_rate method is available")
        else:
            logger.error("❌ generate_subtitles_by_speech_rate method is missing")
            return False
            
        # Check helper methods
        required_methods = [
            '_count_effective_characters',
            '_calculate_pause_time',
            '_get_audio_duration',
            '_calculate_speech_rate',
            '_assign_timestamps_by_speech_rate',
            '_adjust_timestamps_to_duration'
        ]
        
        for method_name in required_methods:
            if hasattr(generator, method_name):
                logger.info(f"✅ {method_name} method is available")
            else:
                logger.error(f"❌ {method_name} method is missing")
                return False
        
        logger.info("🎉 All required methods are available!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Method availability test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting Speech Rate Subtitle Generation Tests")
    
    # Test 1: Method availability
    logger.info("\n" + "="*50)
    logger.info("Test 1: Method Availability")
    logger.info("="*50)
    test1_passed = test_speech_rate_method_availability()
    
    # Test 2: Speech rate calculation
    logger.info("\n" + "="*50)
    logger.info("Test 2: Speech Rate Calculation")
    logger.info("="*50)
    test2_passed = test_speech_rate_calculation()
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("Test Summary")
    logger.info("="*50)
    logger.info(f"Method Availability Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    logger.info(f"Speech Rate Calculation Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        logger.info("🎉 All tests passed! Speech rate method is ready for use.")
    else:
        logger.error("⚠️ Some tests failed. Please check the implementation.")
