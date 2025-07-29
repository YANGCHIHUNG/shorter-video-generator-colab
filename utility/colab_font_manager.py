"""
Colab environment font management for Chinese subtitle support
"""

import os
import subprocess
import logging
import urllib.request
import zipfile
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

class ColabFontManager:
    """Manage fonts in Google Colab environment for Chinese subtitle support"""
    
    def __init__(self):
        self.font_dir = "/usr/share/fonts/truetype/chinese"
        self.font_cache_dir = "/var/cache/fontconfig"
        self.installed_fonts = []
    
    def is_colab_environment(self) -> bool:
        """Check if running in Google Colab"""
        try:
            import google.colab
            return True
        except ImportError:
            return False
    
    def setup_chinese_fonts(self) -> bool:
        """Setup Chinese fonts for Colab environment"""
        if not self.is_colab_environment():
            logger.info("Not in Colab environment, skipping font setup")
            return True
        
        try:
            logger.info("🔤 Setting up Chinese fonts for Colab...")
            
            # Create font directory
            os.makedirs(self.font_dir, exist_ok=True)
            
            # Install system font packages
            self._install_font_packages()
            
            # Download and install additional Chinese fonts
            self._download_noto_fonts()
            
            # Update font cache
            self._update_font_cache()
            
            # Verify installation
            if self._verify_chinese_fonts():
                logger.info("✅ Chinese fonts setup completed successfully!")
                return True
            else:
                logger.warning("⚠️ Font verification failed, but continuing...")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error setting up Chinese fonts: {e}")
            return False
    
    def _install_font_packages(self):
        """Install font packages using apt"""
        packages = [
            "fonts-noto-cjk",
            "fonts-noto-cjk-extra", 
            "fonts-wqy-microhei",
            "fonts-wqy-zenhei",
            "fontconfig"
        ]
        
        logger.info("📦 Installing font packages...")
        
        # Update package list
        subprocess.run(["apt", "update", "-qq"], capture_output=True)
        
        for package in packages:
            try:
                logger.info(f"Installing {package}...")
                result = subprocess.run(
                    ["apt", "install", "-y", "-qq", package], 
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    logger.info(f"✅ {package} installed successfully")
                else:
                    logger.warning(f"⚠️ Failed to install {package}: {result.stderr}")
            except Exception as e:
                logger.warning(f"⚠️ Error installing {package}: {e}")
    
    def _download_noto_fonts(self):
        """Download additional Noto CJK fonts"""
        try:
            logger.info("⬇️ Downloading additional Chinese fonts...")
            
            # Noto Sans CJK SC (Simplified Chinese)
            font_urls = [
                "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTC/NotoSansCJK-Regular.ttc",
                "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTC/NotoSansCJK-Bold.ttc"
            ]
            
            for url in font_urls:
                font_name = url.split("/")[-1]
                font_path = os.path.join(self.font_dir, font_name)
                
                if not os.path.exists(font_path):
                    try:
                        logger.info(f"Downloading {font_name}...")
                        urllib.request.urlretrieve(url, font_path)
                        logger.info(f"✅ Downloaded {font_name}")
                        self.installed_fonts.append(font_path)
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to download {font_name}: {e}")
                else:
                    logger.info(f"✅ {font_name} already exists")
                    
        except Exception as e:
            logger.warning(f"⚠️ Error downloading fonts: {e}")
    
    def _update_font_cache(self):
        """Update system font cache"""
        try:
            logger.info("🔄 Updating font cache...")
            subprocess.run(["fc-cache", "-fv"], capture_output=True)
            logger.info("✅ Font cache updated")
        except Exception as e:
            logger.warning(f"⚠️ Error updating font cache: {e}")
    
    def _verify_chinese_fonts(self) -> bool:
        """Verify that Chinese fonts are available"""
        try:
            # Check for available Chinese fonts
            result = subprocess.run(
                ["fc-list", ":lang=zh"], 
                capture_output=True, text=True
            )
            
            chinese_fonts = result.stdout.strip().split('\n')
            chinese_fonts = [f for f in chinese_fonts if f.strip()]
            
            logger.info(f"Found {len(chinese_fonts)} Chinese fonts:")
            for font in chinese_fonts[:5]:  # Show first 5
                logger.info(f"  - {font.split(':')[0]}")
            
            return len(chinese_fonts) > 0
            
        except Exception as e:
            logger.warning(f"⚠️ Error verifying fonts: {e}")
            return False
    
    def get_best_chinese_font(self) -> str:
        """Get the best available Chinese font for subtitles"""
        # Priority order of fonts to try
        preferred_fonts = [
            "Noto Sans CJK SC",
            "Noto Sans CJK TC", 
            "WenQuanYi Micro Hei",
            "WenQuanYi Zen Hei",
            "DejaVu Sans",
            "Arial"
        ]
        
        try:
            # Get list of available fonts
            result = subprocess.run(
                ["fc-list", ":outline", "-f", "%{family}\n"], 
                capture_output=True, text=True
            )
            available_fonts = set(result.stdout.lower().split('\n'))
            
            # Find the first available preferred font
            for font in preferred_fonts:
                if font.lower() in available_fonts:
                    logger.info(f"✅ Selected font: {font}")
                    return font
            
            # Fallback to first available font
            if available_fonts:
                fallback = list(available_fonts)[0]
                logger.info(f"⚠️ Using fallback font: {fallback}")
                return fallback
                
        except Exception as e:
            logger.warning(f"⚠️ Error detecting fonts: {e}")
        
        # Ultimate fallback
        logger.warning("⚠️ Using ultimate fallback: DejaVu Sans")
        return "DejaVu Sans"
    
    def create_colab_subtitle_style(self, base_style: str = "default") -> str:
        """Create subtitle style optimized for Colab with Chinese support"""
        font_name = self.get_best_chinese_font()
        
        styles = {
            "default": f"FontName={font_name},FontSize=20,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=3,BorderStyle=1",
            "yellow": f"FontName={font_name},FontSize=20,PrimaryColour=&H00ffff,OutlineColour=&H000000,Outline=3,BorderStyle=1",
            "white_box": f"FontName={font_name},FontSize=20,PrimaryColour=&Hffffff,BackColour=&H80000000,BorderStyle=4,MarginV=30",
            "custom": f"FontName={font_name},FontSize=22,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=3,Bold=1,BorderStyle=1"
        }
        
        style = styles.get(base_style, styles["default"])
        logger.info(f"🎨 Created Colab subtitle style: {style}")
        return style

# Global instance
colab_font_manager = ColabFontManager()

def setup_colab_chinese_fonts():
    """Convenience function to setup Chinese fonts in Colab"""
    return colab_font_manager.setup_chinese_fonts()

def get_colab_subtitle_style(style: str = "default") -> str:
    """Get Colab-optimized subtitle style with Chinese support"""
    return colab_font_manager.create_colab_subtitle_style(style)

if __name__ == "__main__":
    # Test font setup
    print("🧪 Testing Colab font setup...")
    
    if colab_font_manager.is_colab_environment():
        print("✅ Running in Colab environment")
        success = colab_font_manager.setup_chinese_fonts()
        if success:
            print("✅ Font setup completed")
            font = colab_font_manager.get_best_chinese_font()
            print(f"✅ Best Chinese font: {font}")
            style = colab_font_manager.create_colab_subtitle_style()
            print(f"✅ Subtitle style: {style}")
        else:
            print("❌ Font setup failed")
    else:
        print("ℹ️ Not in Colab environment, skipping font setup")
