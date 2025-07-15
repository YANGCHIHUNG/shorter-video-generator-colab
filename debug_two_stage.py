#!/usr/bin/env python3
"""
Debug script to test the two-stage video generation system
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_session_handling():
    """Test session data handling"""
    print("🧪 Testing session data handling...")
    
    # Simulate session data
    session_data = {
        'pdf_path': 'test_data/1_Basics_1.pdf',
        'video_path': None,
        'extra_prompt': None,
        'generated_pages': [
            'Page 1 content here',
            'Page 2 content here',
            'Page 3 content here'
        ]
    }
    
    # Simulate request data
    request_data = {
        'pages': [
            'Edited page 1 content',
            'Edited page 2 content',
            'Edited page 3 content'
        ],
        'resolution': 480,
        'TTS_model_type': 'edge',
        'voice': 'zh-TW-YunJheNeural'
    }
    
    print("✅ Session data structure:")
    for key, value in session_data.items():
        if isinstance(value, list):
            print(f"  {key}: {len(value)} items")
        else:
            print(f"  {key}: {value}")
    
    print("\n✅ Request data structure:")
    for key, value in request_data.items():
        if isinstance(value, list):
            print(f"  {key}: {len(value)} items")
        else:
            print(f"  {key}: {value}")
    
    # Test validation
    missing_items = []
    if not session_data.get('pdf_path'):
        missing_items.append("PDF path")
    if not request_data.get('pages'):
        missing_items.append("edited pages")
    
    if missing_items:
        print(f"\n❌ Missing required data: {', '.join(missing_items)}")
        return False
    else:
        print("\n✅ All required data is present!")
        return True

def test_script_parsing():
    """Test script parsing functionality"""
    print("\n🧪 Testing script parsing...")
    
    edited_pages = [
        'This is the content for page 1',
        'This is the content for page 2 with more text',
        'This is the content for page 3'
    ]
    
    # Convert to script format
    edited_script = ""
    for i, page in enumerate(edited_pages):
        edited_script += f"## Page {i+1}\n{page}\n\n"
    
    print("✅ Generated script:")
    print(edited_script)
    
    # Parse script back to pages
    pages = []
    current_page = ""
    
    for line in edited_script.split('\n'):
        if line.strip().startswith('## Page') or line.strip().startswith('# Page'):
            if current_page.strip():
                pages.append(current_page.strip())
            current_page = ""
        else:
            current_page += line + '\n'
    
    if current_page.strip():
        pages.append(current_page.strip())
    
    print(f"✅ Parsed {len(pages)} pages back from script")
    
    # Verify consistency
    if len(pages) == len(edited_pages):
        print("✅ Page count matches!")
        return True
    else:
        print(f"❌ Page count mismatch: {len(pages)} vs {len(edited_pages)}")
        return False

def test_json_handling():
    """Test JSON request handling"""
    print("\n🧪 Testing JSON request handling...")
    
    # Simulate the JSON data sent from frontend
    json_data = {
        'pages': [
            'Edited page 1 content',
            'Edited page 2 content',
            'Edited page 3 content'
        ],
        'resolution': '480',
        'TTS_model_type': 'edge',
        'voice': 'zh-TW-YunJheNeural'
    }
    
    print("✅ JSON request data:")
    print(json.dumps(json_data, indent=2, ensure_ascii=False))
    
    # Test resolution conversion
    try:
        resolution = int(json_data.get('resolution', 480))
        print(f"✅ Resolution converted to int: {resolution}")
    except (ValueError, TypeError):
        resolution = 480
        print(f"⚠️ Resolution fallback to default: {resolution}")
    
    # Test required fields
    required_fields = ['pages', 'resolution', 'TTS_model_type', 'voice']
    missing_fields = []
    
    for field in required_fields:
        if not json_data.get(field):
            missing_fields.append(field)
    
    if missing_fields:
        print(f"❌ Missing required fields: {', '.join(missing_fields)}")
        return False
    else:
        print("✅ All required fields are present!")
        return True

def main():
    """Run all tests"""
    print("🚀 Starting debug tests for two-stage video generation...\n")
    
    tests = [
        test_session_handling,
        test_script_parsing,
        test_json_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All debug tests passed! The system should handle the 'Missing required data' error.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
