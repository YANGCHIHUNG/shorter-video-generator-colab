#!/usr/bin/env python3
"""
Test script for API error handling
測試 API 錯誤處理功能
"""
import os
import sys
import json
import time
from unittest.mock import patch, MagicMock
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utility.api import gemini_chat

def test_503_error_handling():
    """Test handling of 503 service overload errors"""
    print("🧪 Testing 503 Service Overload Error Handling...")
    
    # Create a mock error response
    mock_error = Exception("503 UNAVAILABLE")
    mock_error.status_code = 503
    mock_error.message = "The model is overloaded. Please try again later."
    
    # Mock the genai.Client to raise 503 errors
    with patch('utility.api.genai.Client') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Make the first few calls fail with 503
        mock_client.models.generate_content.side_effect = [
            mock_error,  # First call fails
            mock_error,  # Second call fails
            MagicMock(text="Success after retries!")  # Third call succeeds
        ]
        
        start_time = time.time()
        
        try:
            result = gemini_chat(script="Test prompt")
            end_time = time.time()
            
            print(f"✅ 503 error handling successful!")
            print(f"📊 Total time: {end_time - start_time:.2f} seconds")
            print(f"📝 Result: {result}")
            
            # Verify that multiple calls were made (retry logic)
            assert mock_client.models.generate_content.call_count >= 2
            print(f"🔄 Retry count: {mock_client.models.generate_content.call_count}")
            
        except Exception as e:
            print(f"❌ 503 error handling failed: {e}")
            return False
    
    return True

def test_429_error_handling():
    """Test handling of 429 quota exceeded errors"""
    print("\n🧪 Testing 429 Quota Exceeded Error Handling...")
    
    # Create a mock error response
    mock_error = Exception("429 QUOTA_EXCEEDED")
    mock_error.status_code = 429
    mock_error.message = "Quota exceeded. Please try again later."
    
    # Mock the genai.Client to raise 429 errors
    with patch('utility.api.genai.Client') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Make the first call fail with 429, second succeed
        mock_client.models.generate_content.side_effect = [
            mock_error,  # First call fails
            MagicMock(text="Success after quota retry!")  # Second call succeeds
        ]
        
        start_time = time.time()
        
        try:
            result = gemini_chat(script="Test prompt")
            end_time = time.time()
            
            print(f"✅ 429 error handling successful!")
            print(f"📊 Total time: {end_time - start_time:.2f} seconds")
            print(f"📝 Result: {result}")
            
            # Verify that retry logic was used
            assert mock_client.models.generate_content.call_count >= 2
            print(f"🔄 Retry count: {mock_client.models.generate_content.call_count}")
            
        except Exception as e:
            print(f"❌ 429 error handling failed: {e}")
            return False
    
    return True

def test_client_rotation():
    """Test client rotation mechanism"""
    print("\n🧪 Testing Client Rotation Mechanism...")
    
    # Mock genai.Client to simulate different clients
    with patch('utility.api.genai.Client') as mock_client_class:
        mock_clients = [MagicMock(), MagicMock(), MagicMock()]
        mock_client_class.side_effect = mock_clients
        
        # First client fails, second succeeds
        mock_clients[0].models.generate_content.side_effect = Exception("Client 1 failed")
        mock_clients[1].models.generate_content.return_value = MagicMock(text="Success with client 2!")
        
        try:
            result = gemini_chat(script="Test prompt")
            
            print(f"✅ Client rotation successful!")
            print(f"📝 Result: {result}")
            
            # Verify that multiple clients were created
            assert mock_client_class.call_count >= 2
            print(f"🔄 Client rotation count: {mock_client_class.call_count}")
            
        except Exception as e:
            print(f"❌ Client rotation failed: {e}")
            return False
    
    return True

def test_error_message_formatting():
    """Test error message formatting for different error types"""
    print("\n🧪 Testing Error Message Formatting...")
    
    from config.api_config import USER_FRIENDLY_MESSAGES
    
    # Test different error types
    test_cases = [
        ("503", "過載"),
        ("429", "配額"),
        ("500", "內部錯誤"),
        ("401", "金鑰")
    ]
    
    for status_code, expected_keyword in test_cases:
        if status_code in USER_FRIENDLY_MESSAGES:
            message = USER_FRIENDLY_MESSAGES[status_code]
            if expected_keyword in message:
                print(f"✅ {status_code} error message contains '{expected_keyword}'")
            else:
                print(f"❌ {status_code} error message missing '{expected_keyword}'")
                print(f"   Actual message: {message}")
                return False
        else:
            print(f"❌ {status_code} error message not configured")
            return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Starting API Error Handling Tests...")
    print("=" * 60)
    
    tests = [
        test_503_error_handling,
        test_429_error_handling,
        test_client_rotation,
        test_error_message_formatting
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
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! API error handling is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the error handling implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
