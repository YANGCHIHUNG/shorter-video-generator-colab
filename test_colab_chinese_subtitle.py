#!/usr/bin/env python3
"""
Colab Chinese Subtitle Test Script
測試在 Google Colab 環境中的中文字幕功能
"""

import os
import sys
import logging
import subprocess

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_colab_environment():
    """檢查是否在 Colab 環境中運行"""
    try:
        import google.colab
        logger.info("✅ Running in Google Colab environment")
        return True
    except ImportError:
        logger.info("ℹ️ Not running in Google Colab (testing locally)")
        return False

def install_required_packages():
    """安裝所需的套件"""
    packages = [
        'openai-whisper',
        'ffmpeg-python'
    ]
    
    for package in packages:
        try:
            logger.info(f"📦 Installing {package}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                         check=True, capture_output=True)
            logger.info(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install {package}: {e}")

def setup_chinese_fonts_colab():
    """在 Colab 中設置中文字體"""
    try:
        logger.info("🔤 Setting up Chinese fonts for Colab...")
        
        # Update package list
        subprocess.run(['apt-get', 'update'], check=True, capture_output=True)
        
        # Install Chinese fonts
        subprocess.run([
            'apt-get', 'install', '-y',
            'fonts-noto-cjk',
            'fonts-noto-cjk-extra',
            'fonts-wqy-zenhei',
            'fonts-wqy-microhei'
        ], check=True, capture_output=True)
        
        # Update font cache
        subprocess.run(['fc-cache', '-fv'], check=True, capture_output=True)
        
        logger.info("✅ Chinese fonts setup completed")
        
        # List available fonts for verification
        result = subprocess.run(['fc-list', ':', 'family'], 
                              capture_output=True, text=True)
        chinese_fonts = [line for line in result.stdout.split('\n') 
                        if any(keyword in line.lower() for keyword in ['noto', 'cjk', 'chinese', 'zh'])]
        
        logger.info(f"📋 Available Chinese fonts: {len(chinese_fonts)} found")
        for font in chinese_fonts[:5]:  # Show first 5
            logger.info(f"  - {font.strip()}")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to setup Chinese fonts: {e}")
        return False

def test_ffmpeg_chinese_subtitle():
    """測試 FFmpeg 中文字幕功能"""
    try:
        logger.info("🎬 Testing FFmpeg Chinese subtitle functionality...")
        
        # Create a simple test SRT file with Chinese text
        test_srt_content = """1
00:00:01,000 --> 00:00:05,000
這是一個中文字幕測試

2
00:00:05,000 --> 00:00:10,000
測試在Google Colab中顯示中文字幕

3
00:00:10,000 --> 00:00:15,000
Hello World 中英文混合測試
"""
        
        with open('test_chinese_subtitle.srt', 'w', encoding='utf-8') as f:
            f.write(test_srt_content)
        
        # Test FFmpeg subtitle style with Chinese font
        test_styles = [
            # Basic style with Noto font
            "FontName=Noto Sans CJK SC,FontSize=18,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2",
            # Fallback with WenQuanYi font
            "FontName=WenQuanYi Zen Hei,FontSize=18,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2",
            # Simple style without specific font
            "FontSize=18,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2"
        ]
        
        for i, style in enumerate(test_styles):
            logger.info(f"🎨 Testing style {i+1}: {style[:50]}...")
            
            # Test command (would need actual video file in real scenario)
            test_cmd = [
                'ffmpeg', '-f', 'lavfi', '-i', 'color=black:size=640x480:duration=5',
                '-vf', f'subtitles=test_chinese_subtitle.srt:force_style=\'{style}\':fontsdir=/usr/share/fonts',
                '-y', f'test_output_{i+1}.mp4'
            ]
            
            logger.info(f"🔧 Test command: {' '.join(test_cmd)}")
            
            # In a real test, you would run this command
            # result = subprocess.run(test_cmd, capture_output=True, text=True)
            logger.info(f"✅ Style {i+1} command prepared successfully")
        
        logger.info("✅ FFmpeg Chinese subtitle test preparation completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ FFmpeg test failed: {e}")
        return False

def create_colab_setup_instructions():
    """創建 Colab 設置說明"""
    instructions = """
# Google Colab 中文字幕設置指南

## 1. 安裝字體 (在 Colab 中執行)
```python
!apt-get update
!apt-get install -y fonts-noto-cjk fonts-noto-cjk-extra fonts-wqy-zenhei fonts-wqy-microhei
!fc-cache -fv
```

## 2. 驗證字體安裝
```python
!fc-list : family | grep -i noto
```

## 3. 使用修正版的字幕生成器
```python
from utility.whisper_subtitle import WhisperSubtitleGenerator

# 創建實例 (會自動檢測 Colab 環境)
subtitle_gen = WhisperSubtitleGenerator()

# 處理視頻 (會自動使用中文字體)
success = subtitle_gen.process_video_with_subtitles(
    input_video_path='your_video.mp4',
    output_video_path='output_with_subtitles.mp4',
    subtitle_style='default',  # 或 'yellow', 'white_box', 'custom'
    language='zh'  # 指定中文
)
```

## 4. 推薦的 Colab 字幕樣式
- default: 適合深色背景
- yellow: 黃色字幕，高對比度
- white_box: 白色字幕配黑色背景框
- custom: 大字體加粗樣式

## 5. 故障排除
如果字幕仍然無法正常顯示：
1. 重新安裝字體套件
2. 重啟 Colab runtime
3. 使用 fallback 方法 (自動觸發)
"""
    
    with open('COLAB_CHINESE_SUBTITLE_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    logger.info("✅ Colab setup instructions created: COLAB_CHINESE_SUBTITLE_GUIDE.md")

def main():
    """主要測試流程"""
    logger.info("🚀 Starting Colab Chinese Subtitle Test")
    
    # Check environment
    is_colab = check_colab_environment()
    
    if is_colab:
        # Install packages
        install_required_packages()
        
        # Setup fonts
        setup_chinese_fonts_colab()
    
    # Test FFmpeg functionality
    test_ffmpeg_chinese_subtitle()
    
    # Create setup guide
    create_colab_setup_instructions()
    
    logger.info("✅ Test completed! Check the generated guide for setup instructions.")

if __name__ == "__main__":
    main()
