#!/usr/bin/env python3
"""
Simple test script for API error handling
簡化的 API 錯誤處理測試腳本
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.api_config import USER_FRIENDLY_MESSAGES, RETRY_SUGGESTIONS, ERROR_HANDLING_CONFIG

def test_configuration():
    """Test configuration completeness"""
    print("🧪 Testing Configuration...")
    
    # Test error messages
    required_error_codes = ["503", "429", "500", "401"]
    for code in required_error_codes:
        if code in USER_FRIENDLY_MESSAGES:
            print(f"✅ {code} error message configured")
        else:
            print(f"❌ {code} error message missing")
            return False
    
    # Test retry configurations
    required_configs = ["503_UNAVAILABLE", "429_QUOTA_EXCEEDED", "500_INTERNAL_ERROR"]
    for config in required_configs:
        if config in ERROR_HANDLING_CONFIG:
            print(f"✅ {config} retry configuration found")
        else:
            print(f"❌ {config} retry configuration missing")
            return False
    
    print("✅ All configurations are complete!")
    return True

def test_error_messages():
    """Test error message content"""
    print("\n🧪 Testing Error Message Content...")
    
    test_cases = [
        ("503", "過載"),
        ("429", "配額"),
        ("500", "內部錯誤"),
        ("401", "金鑰")
    ]
    
    for code, keyword in test_cases:
        message = USER_FRIENDLY_MESSAGES.get(code, "")
        if keyword in message:
            print(f"✅ {code} error message contains '{keyword}'")
        else:
            print(f"❌ {code} error message missing '{keyword}'")
            print(f"   Actual: {message}")
            return False
    
    print("✅ All error messages are properly formatted!")
    return True

def test_retry_configurations():
    """Test retry configuration values"""
    print("\n🧪 Testing Retry Configuration Values...")
    
    for config_name, config in ERROR_HANDLING_CONFIG.items():
        required_keys = ["max_retries", "base_delay", "max_delay", "backoff_multiplier"]
        for key in required_keys:
            if key in config:
                print(f"✅ {config_name} has {key}: {config[key]}")
            else:
                print(f"❌ {config_name} missing {key}")
                return False
    
    print("✅ All retry configurations are complete!")
    return True

def main():
    """Run all tests"""
    print("🚀 Starting API Configuration Tests...")
    print("=" * 50)
    
    tests = [
        test_configuration,
        test_error_messages,
        test_retry_configurations
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! API error handling configuration is correct.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
