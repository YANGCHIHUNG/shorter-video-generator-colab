"""
Google Colab 中文字幕修復腳本
在 Colab 中執行此腳本來解決中文字幕顯示問題
"""

import subprocess
import sys
import os

def install_chinese_fonts():
    """安裝中文字體"""
    print("📥 Installing Chinese fonts for Colab...")
    
    try:
        # Update package list
        subprocess.run(['apt-get', 'update'], check=True)
        print("✅ Package list updated")
        
        # Install Chinese fonts
        subprocess.run([
            'apt-get', 'install', '-y',
            'fonts-noto-cjk',
            'fonts-noto-cjk-extra', 
            'fonts-wqy-zenhei',
            'fonts-wqy-microhei',
            'fontconfig'
        ], check=True)
        print("✅ Chinese fonts installed")
        
        # Update font cache
        subprocess.run(['fc-cache', '-fv'], check=True)
        print("✅ Font cache updated")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install fonts: {e}")
        return False

def verify_fonts():
    """驗證字體安裝"""
    print("🔍 Verifying Chinese font installation...")
    
    try:
        result = subprocess.run(['fc-list', ':', 'family'], 
                              capture_output=True, text=True, check=True)
        
        chinese_fonts = []
        for line in result.stdout.split('\n'):
            if any(keyword in line.lower() for keyword in ['noto', 'cjk', 'zh', 'chinese', 'wqy']):
                chinese_fonts.append(line.strip())
        
        print(f"✅ Found {len(chinese_fonts)} Chinese fonts:")
        for font in chinese_fonts[:10]:  # Show first 10
            print(f"  - {font}")
            
        return len(chinese_fonts) > 0
        
    except Exception as e:
        print(f"❌ Font verification failed: {e}")
        return False

def create_test_video():
    """創建測試視頻和字幕"""
    print("🎬 Creating test video and Chinese subtitles...")
    
    # Create test SRT with Chinese text
    srt_content = """1
00:00:01,000 --> 00:00:05,000
這是中文字幕測試

2
00:00:05,000 --> 00:00:10,000
Google Colab 中文顯示測試

3
00:00:10,000 --> 00:00:15,000
測試成功！Chinese test successful!
"""
    
    with open('chinese_test.srt', 'w', encoding='utf-8') as f:
        f.write(srt_content)
    print("✅ Test SRT file created: chinese_test.srt")
    
    # Create simple test video
    try:
        cmd = [
            'ffmpeg', '-f', 'lavfi', 
            '-i', 'color=blue:size=640x480:duration=15',
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
            '-y', 'test_video.mp4'
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        print("✅ Test video created: test_video.mp4")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create test video: {e}")
        return False

def test_chinese_subtitles():
    """測試中文字幕嵌入"""
    print("🧪 Testing Chinese subtitle embedding...")
    
    # Different font options to try
    font_options = [
        "Noto Sans CJK SC",
        "WenQuanYi Zen Hei", 
        "DejaVu Sans",
        "Liberation Sans"
    ]
    
    success_count = 0
    
    for i, font_name in enumerate(font_options):
        try:
            print(f"🎨 Testing font: {font_name}")
            
            # Create subtitle style
            style = f"FontName={font_name},FontSize=20,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2"
            
            # FFmpeg command with explicit font directory
            cmd = [
                'ffmpeg', '-y',
                '-i', 'test_video.mp4',
                '-vf', f'subtitles=chinese_test.srt:force_style=\'{style}\':fontsdir=/usr/share/fonts',
                '-c:a', 'copy',
                f'output_chinese_{i+1}.mp4'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"✅ Success with {font_name}")
                success_count += 1
            else:
                print(f"⚠️ Failed with {font_name}: {result.stderr[:100]}...")
                
        except Exception as e:
            print(f"❌ Error testing {font_name}: {e}")
    
    if success_count > 0:
        print(f"✅ Chinese subtitle test completed! {success_count}/{len(font_options)} fonts worked")
        return True
    else:
        print("❌ All font tests failed")
        return False

def create_colab_instructions():
    """創建 Colab 使用說明"""
    instructions = """# Google Colab 中文字幕解決方案

## 快速設置 (在新的 Colab cell 中執行)

```python
# 1. 安裝必要套件
!pip install openai-whisper ffmpeg-python

# 2. 安裝中文字體
!apt-get update
!apt-get install -y fonts-noto-cjk fonts-noto-cjk-extra fonts-wqy-zenhei fontconfig
!fc-cache -fv

# 3. 驗證字體安裝
!fc-list : family | grep -i noto
```

## 使用修正版字幕生成器

```python
from utility.whisper_subtitle import WhisperSubtitleGenerator

# 初始化 (自動檢測 Colab 環境)
subtitle_gen = WhisperSubtitleGenerator()

# 生成帶中文字幕的視頻
success = subtitle_gen.process_video_with_subtitles(
    input_video_path='your_video.mp4',
    output_video_path='output_with_chinese_subtitles.mp4',
    subtitle_style='default',  # 針對 Colab 優化
    language='zh'  # 中文識別
)

if success:
    print("✅ 中文字幕生成成功！")
else:
    print("❌ 字幕生成失敗，請檢查日誌")
```

## 字幕樣式說明

- `default`: 白色字幕，黑色邊框，適合大多數情況
- `yellow`: 黃色字幕，高對比度
- `white_box`: 白色字幕配半透明黑色背景
- `custom`: 大字體粗體樣式

## 故障排除

1. **字幕無法顯示**：重啟 Runtime 後重新執行字體安裝
2. **中文亂碼**：確保 SRT 文件使用 UTF-8 編碼
3. **FFmpeg 錯誤**：嘗試使用 fallback 方法 (自動觸發)

## 測試成功標誌

如果看到以下訊息，表示設置成功：
- ✅ Chinese fonts installed successfully
- ✅ Colab fonts already available  
- ✅ Subtitles embedded successfully
"""
    
    with open('COLAB_CHINESE_SUBTITLE_SOLUTION.md', 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print("✅ Instructions created: COLAB_CHINESE_SUBTITLE_SOLUTION.md")

def main():
    """主要安裝和測試流程"""
    print("🚀 Google Colab Chinese Subtitle Fix")
    print("=" * 50)
    
    # Step 1: Install fonts
    if not install_chinese_fonts():
        print("❌ Font installation failed!")
        return
    
    # Step 2: Verify installation
    if not verify_fonts():
        print("❌ Font verification failed!")
        return
        
    # Step 3: Create test files
    if not create_test_video():
        print("❌ Test video creation failed!")
        return
    
    # Step 4: Test subtitle embedding
    test_chinese_subtitles()
    
    # Step 5: Create instructions
    create_colab_instructions()
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed!")
    print("📖 Check COLAB_CHINESE_SUBTITLE_SOLUTION.md for usage instructions")

if __name__ == "__main__":
    main()
