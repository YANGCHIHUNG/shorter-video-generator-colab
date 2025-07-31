#!/usr/bin/env python3
"""
Test script for subtitle functionality
"""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utility.whisper_subtitle import WhisperSubtitleGenerator, check_whisper_dependencies

def test_dependencies():
    """Test if all required dependencies are available"""
    print("🔍 Checking dependencies...")
    deps = check_whisper_dependencies()
    
    all_available = True
    for dep, available in deps.items():
        status = "✅" if available else "❌"
        print(f"{status} {dep}: {'Available' if available else 'Missing'}")
        if not available:
            all_available = False
    
    if not all_available:
        print("\n⚠️ Some dependencies are missing. Please install:")
        if not deps.get('ffmpeg', False):
            print("   - FFmpeg: https://ffmpeg.org/download.html")
        if not deps.get('whisper', False):
            print("   - OpenAI Whisper: pip install openai-whisper")
        return False
    
    print("✅ All dependencies are available!")
    return True

def test_subtitle_generator():
    """Test the WhisperSubtitleGenerator class"""
    if not test_dependencies():
        return False
    
    print("\n🧪 Testing WhisperSubtitleGenerator...")
    
    try:
        # Initialize subtitle generator
        subtitle_gen = WhisperSubtitleGenerator()
        print("✅ WhisperSubtitleGenerator initialized successfully")
        
        # Test loading Whisper model
        subtitle_gen.load_whisper_model("tiny")  # Use smallest model for testing
        print("✅ Whisper model loaded successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing WhisperSubtitleGenerator: {e}")
        return False

def create_test_video():
    """Create a simple test video with audio for testing"""
    try:
        import numpy as np
        from moviepy.editor import AudioClip, ImageClip, CompositeVideoClip
        
        # Create a simple 5-second test audio (sine wave)
        def make_frame_audio(t):
            return np.sin(440 * 2 * np.pi * t)  # 440 Hz tone
        
        # Create a simple image (black square)
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Create video and audio clips
        audio_clip = AudioClip(make_frame_audio, duration=5)
        video_clip = ImageClip(image, duration=5).set_audio(audio_clip)
        
        # Export test video
        test_video_path = "test_video.mp4"
        video_clip.write_videofile(
            test_video_path,
            fps=24,
            verbose=False,
            logger=None
        )
        
        video_clip.close()
        print(f"✅ Test video created: {test_video_path}")
        return test_video_path
        
    except Exception as e:
        print(f"❌ Error creating test video: {e}")
        return None

def test_full_pipeline():
    """Test the complete subtitle pipeline"""
    if not test_dependencies():
        return False
    
    print("\n🔄 Testing full subtitle pipeline...")
    
    # Create test video
    test_video_path = create_test_video()
    if not test_video_path:
        return False
    
    try:
        subtitle_gen = WhisperSubtitleGenerator()
        
        # Test the complete pipeline
        output_video_path = "test_video_with_subtitles.mp4"
        success = subtitle_gen.process_video_with_subtitles(
            input_video_path=test_video_path,
            output_video_path=output_video_path,
            subtitle_style="default"
        )
        
        if success and os.path.exists(output_video_path):
            print("✅ Full subtitle pipeline test successful!")
            
            # Clean up test files
            os.remove(test_video_path)
            os.remove(output_video_path)
            
            return True
        else:
            print("❌ Full subtitle pipeline test failed")
            return False
            
    except Exception as e:
        print(f"❌ Error in full pipeline test: {e}")
        
        # Clean up test files
        if test_video_path and os.path.exists(test_video_path):
            os.remove(test_video_path)
        
        return False

def main():
    """Run all tests"""
    print("🎬 Subtitle Functionality Test Suite")
    print("=" * 40)
    
    success = True
    
    # Test 1: Dependencies
    if not test_dependencies():
        success = False
    
    # Test 2: SubtitleGenerator
    if not test_subtitle_generator():
        success = False
    
    # Test 3: Full pipeline (optional, requires more resources)
    # Uncomment the following lines to test the full pipeline
    # if not test_full_pipeline():
    #     success = False
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 All tests passed! Subtitle functionality is ready.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
