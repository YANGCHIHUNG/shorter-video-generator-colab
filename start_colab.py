#!/usr/bin/env python3
"""
Google Colab 專用啟動腳本
處理音頻系統警告並設置適當的環境變數
"""

import os
import sys
import warnings
import subprocess

def setup_colab_environment():
    """設置 Colab 環境變數和警告抑制"""
    print("🔧 Setting up Google Colab environment...")
    
    # Set environment variables to suppress audio warnings
    os.environ.setdefault('ALSA_PCM_CARD', '0')
    os.environ.setdefault('ALSA_PCM_DEVICE', '0')
    os.environ.setdefault('XDG_RUNTIME_DIR', '/tmp/runtime-root')
    os.environ.setdefault('PULSE_RUNTIME_PATH', '/tmp/pulse')
    
    # Create runtime directories
    runtime_dirs = ['/tmp/runtime-root', '/tmp/pulse']
    for dir_path in runtime_dirs:
        try:
            os.makedirs(dir_path, exist_ok=True)
            os.chmod(dir_path, 0o700)
        except Exception as e:
            print(f"⚠️ Could not create {dir_path}: {e}")
    
    # Suppress various warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
    # Suppress ALSA warnings at system level
    os.environ['PYTHONWARNINGS'] = 'ignore'
    
    print("✅ Colab environment setup completed")

def install_dependencies():
    """安裝 Colab 所需依賴項"""
    print("📦 Installing dependencies for Colab...")
    
    try:
        # Install essential packages
        packages = [
            'openai-whisper',
            'ffmpeg-python',
            'edge-tts'
        ]
        
        for package in packages:
            print(f"📥 Installing {package}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                         check=True, capture_output=True)
        
        print("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_chinese_fonts():
    """設置中文字體支援"""
    print("🔤 Setting up Chinese font support...")
    
    try:
        # Update package list and install fonts
        commands = [
            ['apt-get', 'update'],
            ['apt-get', 'install', '-y', 'fonts-noto-cjk', 'fonts-noto-cjk-extra', 'fonts-wqy-zenhei', 'fontconfig'],
            ['fc-cache', '-fv']
        ]
        
        for cmd in commands:
            subprocess.run(cmd, check=True, capture_output=True)
        
        print("✅ Chinese fonts setup completed")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to setup fonts: {e}")
        return False

def start_flask_app():
    """啟動 Flask 應用程式"""
    print("🚀 Starting Flask application...")
    
    try:
        # Import and run the app
        from app import app
        
        # Run in Colab-friendly mode
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,  # Disable debug mode in Colab
            use_reloader=False  # Disable reloader in Colab
        )
        
    except Exception as e:
        print(f"❌ Failed to start Flask app: {e}")
        return False

def main():
    """主要設置和啟動流程"""
    print("🎬 Google Colab Video Generator Setup")
    print("=" * 50)
    
    # Step 1: Setup environment
    setup_colab_environment()
    
    # Step 2: Install dependencies (optional, comment out if already installed)
    # install_dependencies()
    
    # Step 3: Setup Chinese fonts (optional, comment out if already setup)
    # setup_chinese_fonts()
    
    # Step 4: Start Flask app
    print("\n🌟 Environment setup completed!")
    print("🔗 Your app will be available at: http://localhost:5000")
    print("💡 In Colab, use: from google.colab.output import eval_js; print(eval_js('google.colab.kernel.proxyPort(5000)'))")
    
    start_flask_app()

if __name__ == "__main__":
    main()
