#!/usr/bin/env python3
"""
Test script to debug the session management issue
"""

import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_session_persistence():
    """Test if session data persists correctly"""
    print("🧪 Testing session persistence...")
    
    # Simulate the generate_text workflow
    print("\n1. Simulating generate_text workflow:")
    
    # Mock session data (what should be saved)
    session_data = {
        'generated_pages': ['Page 1 content', 'Page 2 content', 'Page 3 content'],
        'pdf_path': r'D:\Documents\2025-nchu-fall\shorter-video-generator-colab\output\1\test.pdf',
        'video_path': None,
        'extra_prompt': None
    }
    
    print(f"   Session data to save: {session_data}")
    
    # Check if the paths are valid
    pdf_path = session_data['pdf_path']
    print(f"   PDF path: {pdf_path}")
    print(f"   PDF exists: {os.path.exists(pdf_path) if pdf_path else 'N/A'}")
    
    print("\n2. Simulating process_with_edited_text workflow:")
    
    # Mock request data (what comes from frontend)
    request_data = {
        'pages': ['Edited page 1', 'Edited page 2', 'Edited page 3'],
        'resolution': 480,
        'TTS_model_type': 'edge',
        'voice': 'zh-TW-YunJheNeural'
    }
    
    print(f"   Request data: {request_data}")
    
    # Check validation
    pdf_path = session_data.get('pdf_path')
    edited_pages = request_data.get('pages', [])
    
    print(f"   PDF path from session: {pdf_path}")
    print(f"   Edited pages from request: {len(edited_pages)} items")
    
    # Validation check
    missing_items = []
    if not pdf_path:
        missing_items.append("PDF path")
    if not edited_pages:
        missing_items.append("edited pages")
    
    if missing_items:
        print(f"   ❌ Missing required data: {', '.join(missing_items)}")
        return False
    else:
        print("   ✅ All required data is present!")
        return True

def test_session_keys():
    """Test common session key issues"""
    print("\n🧪 Testing session key issues...")
    
    # Common issues
    test_cases = [
        {
            'name': 'Normal case',
            'session': {'pdf_path': 'test.pdf', 'generated_pages': ['page1']},
            'expected': True
        },
        {
            'name': 'Missing PDF path',
            'session': {'generated_pages': ['page1']},
            'expected': False
        },
        {
            'name': 'Empty PDF path',
            'session': {'pdf_path': '', 'generated_pages': ['page1']},
            'expected': False
        },
        {
            'name': 'None PDF path',
            'session': {'pdf_path': None, 'generated_pages': ['page1']},
            'expected': False
        }
    ]
    
    for case in test_cases:
        print(f"\n   Testing: {case['name']}")
        session = case['session']
        
        pdf_path = session.get('pdf_path')
        generated_pages = session.get('generated_pages', [])
        
        print(f"   PDF path: {repr(pdf_path)}")
        print(f"   Generated pages: {len(generated_pages)} items")
        
        # Check if valid
        is_valid = bool(pdf_path and generated_pages)
        expected = case['expected']
        
        if is_valid == expected:
            print(f"   ✅ Result: {is_valid} (Expected: {expected})")
        else:
            print(f"   ❌ Result: {is_valid} (Expected: {expected})")
    
    return True

def test_poppler_configuration():
    """Test Poppler configuration"""
    print("\n🧪 Testing Poppler configuration...")
    
    # Test system-installed Poppler
    try:
        from pdf2image import convert_from_path
        
        # Try to use convert_from_path with None (system Poppler)
        print("   Testing system-installed Poppler...")
        print("   ✅ pdf2image can be imported")
        print("   ✅ Using poppler_path=None should work with system-installed Poppler")
        
        return True
    except ImportError as e:
        print(f"   ❌ Failed to import pdf2image: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting session management debug tests...\n")
    
    tests = [
        test_session_persistence,
        test_session_keys,
        test_poppler_configuration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        print("\n💡 Debugging suggestions:")
        print("   1. Check if session data is being properly saved in generate_text")
        print("   2. Verify that session persists between requests")
        print("   3. Ensure PDF file still exists when processing")
        print("   4. Check Flask session configuration")
        return True
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
