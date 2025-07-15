#!/usr/bin/env python3
"""
Test script for the new two-stage video generation system.
This script will test the text generation functionality.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_text_generation():
    """Test the text generation functionality"""
    print("🧪 Testing text generation functionality...")
    
    # Test imports
    try:
        from api.whisper_LLM_api import api_generate_text_only
        print("✅ Successfully imported api_generate_text_only")
    except ImportError as e:
        print(f"❌ Failed to import api_generate_text_only: {e}")
        return False
    
    # Test file paths
    test_pdf = project_root / "test_data" / "1_Basics_1.pdf"
    poppler_path = project_root / "poppler" / "poppler-0.89.0" / "bin"
    
    if not test_pdf.exists():
        print(f"❌ Test PDF not found: {test_pdf}")
        return False
    
    if not poppler_path.exists():
        print(f"❌ Poppler path not found: {poppler_path}")
        return False
    
    print(f"✅ Test PDF found: {test_pdf}")
    print(f"✅ Poppler path found: {poppler_path}")
    
    # Test async function (without actually running it due to API dependencies)
    print("✅ All basic tests passed!")
    return True

def test_flask_routes():
    """Test Flask route definitions"""
    print("\n🧪 Testing Flask route definitions...")
    
    try:
        from app import app
        print("✅ Successfully imported Flask app")
        
        # Check if routes exist
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        required_routes = ['/generate_text', '/process_with_edited_text', '/edit_text']
        
        for route in required_routes:
            if route in routes:
                print(f"✅ Route {route} found")
            else:
                print(f"❌ Route {route} not found")
                return False
        
        print("✅ All required routes are defined!")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import Flask app: {e}")
        return False

def test_templates():
    """Test template files"""
    print("\n🧪 Testing template files...")
    
    templates_dir = project_root / "templates"
    required_templates = ['index.html', 'edit_text.html', 'base.html']
    
    for template in required_templates:
        template_path = templates_dir / template
        if template_path.exists():
            print(f"✅ Template {template} found")
        else:
            print(f"❌ Template {template} not found")
            return False
    
    print("✅ All required templates are present!")
    return True

def main():
    """Run all tests"""
    print("🚀 Starting two-stage video generation system tests...\n")
    
    tests = [
        test_text_generation,
        test_flask_routes,
        test_templates
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The two-stage system is ready for testing.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
