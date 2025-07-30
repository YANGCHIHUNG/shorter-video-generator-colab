"""
Whisper-based subtitle generation and embedding utilities
針對 Google Colab 環境優化的中文字幕生成器
支援簡體/繁體中文字幕轉換
"""

import os
import tempfile
import subprocess
import logging
from typing import Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhisperSubtitleGenerator:
    """Generate and embed subtitles using OpenAI Whisper and FFmpeg"""
    
    def __init__(self, traditional_chinese: bool = False):
        """Initialize the Whisper subtitle generator
        
        Args:
            traditional_chinese: If True, convert simplified Chinese to traditional Chinese
        """
        try:
            import whisper
            self.whisper = whisper
            self.model = None
            self.model_size = "small"  # Default model size
            self.colab_fonts_setup = False  # Track if Colab fonts are setup
            self.traditional_chinese = traditional_chinese  # Chinese conversion setting
            
            logger.info(f"🇹🇼 Traditional Chinese mode: {'ENABLED' if self.traditional_chinese else 'DISABLED'}")
            
            # Initialize Chinese converter if needed
            if self.traditional_chinese:
                try:
                    import zhconv
                    self.zhconv = zhconv
                    self.use_zhconv = True
                    logger.info("✅ Traditional Chinese conversion enabled (using zhconv)")
                except ImportError:
                    logger.info("💡 zhconv not available, using built-in conversion table")
                    self.use_zhconv = False
                    # Initialize built-in conversion table
                    self._init_builtin_conversion_table()
            else:
                self.use_zhconv = False
            
            # Suppress audio warnings for Colab
            os.environ['ALSA_PCM_CARD'] = '0'
            os.environ['ALSA_PCM_DEVICE'] = '0'
            
            logger.info("✅ WhisperSubtitleGenerator initialized successfully")
        except ImportError:
            # Allow initialization without Whisper for testing purposes
            logger.warning("⚠️ Whisper not installed, running in test mode")
            self.whisper = None
            self.model = None
            self.model_size = "small"
            self.colab_fonts_setup = False
            self.traditional_chinese = traditional_chinese
            
            logger.info(f"🇹🇼 Traditional Chinese mode: {'ENABLED' if self.traditional_chinese else 'DISABLED'}")
            
            # Initialize Chinese converter if needed
            if self.traditional_chinese:
                try:
                    import zhconv
                    self.zhconv = zhconv
                    self.use_zhconv = True
                    logger.info("✅ Traditional Chinese conversion enabled (using zhconv)")
                except ImportError:
                    logger.info("💡 zhconv not available, using built-in conversion table")
                    self.use_zhconv = False
                    # Initialize built-in conversion table
                    self._init_builtin_conversion_table()
            else:
                self.use_zhconv = False
            
            logger.info("✅ WhisperSubtitleGenerator initialized in test mode")
        except Exception as e:
            logger.error(f"❌ Failed to load subtitle model: {e}")
            raise
    
    def _is_colab_environment(self) -> bool:
        """Check if running in Google Colab"""
        try:
            # Check for Colab specific environment variables and modules
            colab_indicators = [
                'COLAB_GPU' in os.environ,
                'COLAB_TPU_PROXY' in os.environ,
                '/content' in os.getcwd(),
                os.path.exists('/usr/local/lib/python3.10/dist-packages/google/colab')
            ]
            
            is_colab = any(colab_indicators)
            if is_colab:
                logger.info("✅ Detected Google Colab environment")
            return is_colab
        except Exception:
            return False
    
    def _setup_colab_fonts_if_needed(self):
        """Setup Chinese fonts in Colab if not already done"""
        if not self._is_colab_environment():
            return
            
        try:
            logger.info("🔤 Setting up Chinese fonts for Colab...")
            
            # Check if fonts are already installed
            font_check_cmd = ['fc-list', ':', 'family']
            result = subprocess.run(font_check_cmd, capture_output=True, text=True)
            
            if 'Noto' not in result.stdout:
                logger.info("📥 Installing Chinese fonts...")
                
                # Install fonts with apt
                install_cmds = [
                    ['apt-get', 'update'],
                    ['apt-get', 'install', '-y', 'fonts-noto-cjk', 'fonts-noto-cjk-extra', 'fonts-wqy-zenhei', 'fontconfig']
                ]
                
                for cmd in install_cmds:
                    subprocess.run(cmd, check=True, capture_output=True)
                
                # Update font cache
                subprocess.run(['fc-cache', '-fv'], check=True, capture_output=True)
                
                logger.info("✅ Chinese fonts installed successfully")
            else:
                logger.info("✅ Chinese fonts already available")
                
            self.colab_fonts_setup = True
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to setup Colab fonts: {e}")
            self.colab_fonts_setup = False
    
    def _get_standard_subtitle_style(self, style_type: str) -> str:
        """Get standard subtitle styles for local environment"""
        styles = {
            "default": "FontName=Arial,FontSize=16,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2",
            "yellow": "FontName=Arial,FontSize=16,PrimaryColour=&H00ffff,OutlineColour=&H000000,Outline=2",
            "white_box": "FontName=Arial,FontSize=16,PrimaryColour=&Hffffff,BackColour=&H000000,BorderStyle=4",
            "custom": "FontName=Arial,FontSize=18,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Bold=1"
        }
        return styles.get(style_type, styles["default"])
    
    def _get_colab_subtitle_style(self, style_type: str) -> str:
        """Get Colab-optimized subtitle styles with Chinese font support"""
        # Choose font based on Chinese preference
        if self.traditional_chinese:
            base_font = "Noto Sans CJK TC"  # Traditional Chinese font
            logger.debug("🔤 Using Traditional Chinese font: Noto Sans CJK TC")
        else:
            base_font = "Noto Sans CJK SC"  # Simplified Chinese font
            logger.debug("🔤 Using Simplified Chinese font: Noto Sans CJK SC")
        
        styles = {
            "default": f"FontName={base_font},FontSize=20,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=3,Shadow=1",
            "yellow": f"FontName={base_font},FontSize=20,PrimaryColour=&H00ffff,OutlineColour=&H000000,Outline=3,Shadow=1",
            "white_box": f"FontName={base_font},FontSize=20,PrimaryColour=&Hffffff,BackColour=&H80000000,BorderStyle=4,MarginV=20",
            "custom": f"FontName={base_font},FontSize=22,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=3,Bold=1,Shadow=2"
        }
        return styles.get(style_type, styles["default"])
    
    def _create_colab_ffmpeg_command(self, input_video: str, srt_path: str, 
                                   output_video: str, style: str) -> list:
        """Create FFmpeg command optimized for Colab environment"""
        return [
            'ffmpeg', '-y',  # Overwrite output
            '-i', input_video,
            '-vf', f'subtitles={srt_path}:force_style=\'{style}\':fontsdir=/usr/share/fonts:/usr/share/fonts/truetype',
            '-c:a', 'copy',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',  # Good quality balance
            output_video
        ]
    
    def _embed_subtitles_colab_fallback(self, input_video: str, srt_path: str, 
                                      output_video: str, style_type: str) -> bool:
        """Fallback method for Colab subtitle embedding"""
        try:
            logger.info("🔄 Using Colab fallback subtitle method...")
            
            # Multiple fallback attempts
            fallback_commands = [
                # Attempt 1: WenQuanYi font
                [
                    'ffmpeg', '-y', '-i', input_video,
                    '-vf', f'subtitles={srt_path}:force_style=\'FontName=WenQuanYi Zen Hei,FontSize=20\'',
                    '-c:a', 'copy', output_video
                ],
                # Attempt 2: Simple subtitle without font specification
                [
                    'ffmpeg', '-y', '-i', input_video,
                    '-vf', f'subtitles={srt_path}',
                    '-c:a', 'copy', output_video
                ],
                # Attempt 3: Basic ASS subtitle
                [
                    'ffmpeg', '-y', '-i', input_video,
                    '-vf', f'ass={srt_path}',
                    '-c:a', 'copy', output_video
                ]
            ]
            
            for i, cmd in enumerate(fallback_commands):
                try:
                    logger.info(f"🔄 Fallback attempt {i+1}/3...")
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    
                    if result.returncode == 0:
                        logger.info(f"✅ Fallback method {i+1} successful!")
                        return True
                    else:
                        logger.warning(f"⚠️ Fallback attempt {i+1} failed: {result.stderr[:100]}...")
                        
                except subprocess.TimeoutExpired:
                    logger.warning(f"⚠️ Fallback attempt {i+1} timed out")
                except Exception as e:
                    logger.warning(f"⚠️ Fallback attempt {i+1} error: {e}")
            
            logger.error("❌ All fallback methods failed")
            return False
                
        except Exception as e:
            logger.error(f"❌ Fallback method error: {e}")
            return False

    def _normalize_language_code(self, language: str) -> Optional[str]:
        """Normalize language code for Whisper compatibility"""
        if not language:
            return None
            
        language = language.lower().strip()
        
        # Handle common language codes and mappings
        language_mapping = {
            'auto': None,  # Auto-detection
            'zh': 'zh',    # Chinese
            'zh-cn': 'zh', # Simplified Chinese
            'zh-tw': 'zh', # Traditional Chinese  
            'zh-hk': 'zh', # Hong Kong Chinese
            'en': 'en',    # English
            'en-us': 'en', # US English
            'en-gb': 'en', # UK English
            'ja': 'ja',    # Japanese
            'ko': 'ko',    # Korean
            'es': 'es',    # Spanish
            'fr': 'fr',    # French
            'de': 'de',    # German
            'it': 'it',    # Italian
            'pt': 'pt',    # Portuguese
            'ru': 'ru',    # Russian
            'ar': 'ar',    # Arabic
            'hi': 'hi',    # Hindi
        }
        
        # Check if it's a known language code
        if language in language_mapping:
            normalized = language_mapping[language]
            if normalized:
                logger.info(f"🔄 Language code normalized: {language} → {normalized}")
            return normalized
        
        # Check if it's already a valid Whisper language
        whisper_languages = [
            'en', 'zh', 'de', 'es', 'ru', 'ko', 'fr', 'ja', 'pt', 'tr', 'pl', 'ca', 'nl', 
            'ar', 'sv', 'it', 'id', 'hi', 'fi', 'vi', 'he', 'uk', 'el', 'ms', 'cs', 'ro', 
            'da', 'hu', 'ta', 'no', 'th', 'ur', 'hr', 'bg', 'lt', 'la', 'mi', 'ml', 'cy', 
            'sk', 'te', 'fa', 'lv', 'bn', 'sr', 'az', 'sl', 'kn', 'et', 'mk', 'br', 'eu', 
            'is', 'hy', 'ne', 'mn', 'bs', 'kk', 'sq', 'sw', 'gl', 'mr', 'pa', 'si', 'km', 
            'sn', 'yo', 'so', 'af', 'oc', 'ka', 'be', 'tg', 'sd', 'gu', 'am', 'yi', 'lo', 
            'uz', 'fo', 'ht', 'ps', 'tk', 'nn', 'mt', 'sa', 'lb', 'my', 'bo', 'tl', 'mg', 
            'as', 'tt', 'haw', 'ln', 'ha', 'ba', 'jw', 'su'
        ]
        
        if language in whisper_languages:
            logger.info(f"✅ Valid Whisper language code: {language}")
            return language
        
        logger.warning(f"⚠️ Unrecognized language code: {language}")
        return None
    
    def _init_builtin_conversion_table(self):
        """Initialize built-in simplified to traditional Chinese conversion table"""
        self.s2t_table = {
            # 基本常用字
            '这': '這', '个': '個', '中': '中', '文': '文', '测': '測', '试': '試',
            '简': '簡', '体': '體', '繁': '繁', '转': '轉', '换': '換',
            
            # 技術詞彙
            '人': '人', '工': '工', '智': '智', '能': '能', '语': '語', '音': '音',
            '识': '識', '别': '別', '技': '技', '术': '術',
            
            # 視頻相關
            '视': '視', '频': '頻', '字': '字', '幕': '幕', '自': '自', '动': '動',
            '生': '生', '成': '成', '系': '系', '统': '統',
            
            # 學習機器相關
            '机': '機', '器': '器', '学': '學', '习': '習', '和': '和', '深': '深',
            '度': '度', '习': '習',
            
            # 常用詞
            '是': '是', '一': '一', '了': '了', '在': '在', '有': '有', '的': '的',
            '我': '我', '你': '你', '他': '他', '她': '她', '它': '它',
            '们': '們', '来': '來', '去': '去', '说': '說', '话': '話',
            '时': '時', '间': '間', '地': '地', '方': '方', '问': '問', '题': '題',
            '内': '內', '容': '容', '混': '混', '合': '合', '言': '言',
            '第': '第', '段': '段', '会': '會', '将': '將', '对': '對', '于': '於',
            '为': '為', '与': '與', '从': '從', '到': '到', '过': '過', '得': '得',
            '应': '應', '该': '該', '让': '讓', '给': '給', '没': '沒', '还': '還',
            '后': '後', '前': '前', '下': '下', '上': '上', '里': '裡', '外': '外',
            '开': '開', '关': '關', '进': '進', '出': '出', '入': '入',
            '处': '處', '理': '理', '做': '做', '用': '用', '可': '可',
            '要': '要', '想': '想', '看': '看', '听': '聽', '读': '讀', '写': '寫',
            
            # 數字和標點保持不變
            '0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', 
            '6': '6', '7': '7', '8': '8', '9': '9',
        }
        logger.info(f"✅ Built-in conversion table initialized with {len(self.s2t_table)} characters")
    
    def _builtin_convert_to_traditional(self, text: str) -> str:
        """Convert text using built-in conversion table"""
        result = ""
        for char in text:
            if char in self.s2t_table:
                result += self.s2t_table[char]
            else:
                result += char  # Keep original character
        return result
    
    def _convert_to_traditional_chinese(self, text: str) -> str:
        """Convert simplified Chinese text to traditional Chinese"""
        if not self.traditional_chinese:
            return text
        
        try:
            if self.use_zhconv and hasattr(self, 'zhconv'):
                # Use zhconv library if available
                converted = self.zhconv.convert(text, 'zh-tw')
                logger.info(f"🔄 Converted using zhconv: {text[:30]}... → {converted[:30]}...")
                return converted
            else:
                # Use built-in conversion table
                converted = self._builtin_convert_to_traditional(text)
                logger.info(f"🔄 Converted using built-in table: {text[:30]}... → {converted[:30]}...")
                return converted
        except Exception as e:
            logger.warning(f"⚠️ Failed to convert to traditional Chinese: {e}")
            return text
    
    def _detect_and_convert_chinese(self, text: str) -> str:
        """Detect Chinese content and convert if needed"""
        if not self.traditional_chinese:
            return text
        
        # Check if text contains Chinese characters
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        if chinese_chars > 0:
            logger.info(f"🔄 Converting Chinese text: {text[:50]}...")
            converted = self._convert_to_traditional_chinese(text)
            logger.info(f"✅ Conversion result: {converted[:50]}...")
            return converted
        
        return text

    def load_model(self, model_size: str = "small"):
        """Load Whisper model with specified size"""
        try:
            logger.info(f"📥 Loading Whisper model: {model_size}")
            
            # Suppress PyTorch warnings in Colab
            import warnings
            warnings.filterwarnings("ignore", category=UserWarning)
            
            self.model = self.whisper.load_model(model_size)
            self.model_size = model_size
            logger.info(f"✅ Whisper model loaded: {model_size}")
        except Exception as e:
            logger.error(f"❌ Failed to load Whisper model: {e}")
            raise

    def extract_audio_from_video(self, video_path: str, audio_path: Optional[str] = None) -> str:
        """Extract audio from video file using FFmpeg"""
        try:
            if audio_path is None:
                audio_path = video_path.rsplit('.', 1)[0] + '_temp_audio.wav'
            
            logger.info(f"🎵 Extracting audio from: {os.path.basename(video_path)}")
            
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',
                '-ar', '16000',  # 16kHz for Whisper
                '-ac', '1',  # Mono
                audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Audio extracted: {os.path.basename(audio_path)}")
                return audio_path
            else:
                logger.error(f"❌ Audio extraction failed: {result.stderr}")
                raise Exception(f"Audio extraction failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"❌ Error extracting audio: {e}")
            raise

    def generate_srt_from_audio(self, audio_path: str, srt_path: Optional[str] = None, 
                              language: Optional[str] = None) -> str:
        """Generate SRT subtitle file from audio using Whisper"""
        try:
            if self.model is None:
                self.load_model(self.model_size)
            
            if srt_path is None:
                srt_path = audio_path.rsplit('.', 1)[0] + '.srt'
            
            logger.info(f"🤖 Generating subtitles from audio...")
            
            # Handle language parameter - Whisper doesn't support "auto"
            whisper_language = None
            if language and language.lower() != "auto":
                # Validate and convert language codes
                whisper_language = self._normalize_language_code(language)
                if whisper_language:
                    logger.info(f"🌍 Using specified language: {whisper_language}")
                else:
                    logger.warning(f"⚠️ Invalid language code '{language}', using auto-detection")
            else:
                logger.info("🌍 Using automatic language detection")
            
            # Whisper transcription options
            options = {
                "word_timestamps": True,
                "verbose": False
            }
            
            # Only add language if it's valid
            if whisper_language:
                options["language"] = whisper_language
            
            logger.info(f"🔧 Whisper options: {options}")
            
            result = self.model.transcribe(audio_path, **options)
            
            # Generate SRT content
            srt_content = self._create_srt_from_segments(result["segments"])
            
            # Write SRT file with UTF-8 encoding
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            logger.info(f"✅ SRT file generated: {os.path.basename(srt_path)}")
            return srt_path
            
        except Exception as e:
            logger.error(f"❌ Error generating SRT: {e}")
            raise

    def _create_srt_from_segments(self, segments) -> str:
        """Create SRT content from Whisper segments with optional traditional Chinese conversion"""
        srt_content = ""
        
        for i, segment in enumerate(segments, 1):
            start_time = self._format_timestamp(segment['start'])
            end_time = self._format_timestamp(segment['end'])
            text = segment['text'].strip()
            
            # Apply traditional Chinese conversion if enabled
            if self.traditional_chinese:
                text = self._detect_and_convert_chinese(text)
            
            srt_content += f"{i}\n"
            srt_content += f"{start_time} --> {end_time}\n"
            srt_content += f"{text}\n\n"
        
        return srt_content

    def _format_timestamp(self, seconds: float) -> str:
        """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

    def embed_subtitles_in_video(self, input_video_path: str, srt_path: str, 
                               output_video_path: str, subtitle_style: str = "default") -> bool:
        """Embed SRT subtitles into video using FFmpeg with Chinese support"""
        try:
            logger.info(f"🎬 Embedding subtitles into video...")
            
            # Check environment and setup fonts
            is_colab = self._is_colab_environment()
            if is_colab:
                if not self.colab_fonts_setup:
                    self._setup_colab_fonts_if_needed()
                style = self._get_colab_subtitle_style(subtitle_style)
                cmd = self._create_colab_ffmpeg_command(
                    input_video_path, srt_path, output_video_path, style
                )
            else:
                style = self._get_standard_subtitle_style(subtitle_style)
                cmd = [
                    'ffmpeg', '-y', '-i', input_video_path,
                    '-vf', f'subtitles={srt_path}:force_style=\'{style}\'',
                    '-c:a', 'copy',
                    output_video_path
                ]
            
            logger.info(f"🎨 Using subtitle style: {subtitle_style}")
            
            # Execute FFmpeg command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                logger.info(f"✅ Subtitles embedded successfully")
                return True
            else:
                logger.warning(f"⚠️ Primary method failed: {result.stderr[:200]}...")
                
                # Try fallback for Colab
                if is_colab:
                    logger.info("🔄 Trying Colab fallback methods...")
                    return self._embed_subtitles_colab_fallback(
                        input_video_path, srt_path, output_video_path, subtitle_style
                    )
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Subtitle embedding timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Error embedding subtitles: {e}")
            return False

    def process_video_with_subtitles(self, input_video_path: str, output_video_path: str,
                                   subtitle_style: str = "default", 
                                   language: Optional[str] = None,
                                   cleanup_temp_files: bool = True) -> bool:
        """Complete pipeline: extract audio, generate subtitles, embed in video"""
        temp_files = []
        
        try:
            logger.info(f"🎬 Starting subtitle processing pipeline...")
            logger.info(f"📁 Input: {os.path.basename(input_video_path)}")
            logger.info(f"📁 Output: {os.path.basename(output_video_path)}")
            
            # Setup Colab environment if needed
            if self._is_colab_environment():
                self._setup_colab_fonts_if_needed()
            
            # Step 1: Extract audio
            logger.info("📍 Step 1/3: Extracting audio...")
            audio_path = self.extract_audio_from_video(input_video_path)
            temp_files.append(audio_path)
            
            # Step 2: Generate SRT
            logger.info("📍 Step 2/3: Generating subtitles...")
            srt_path = self.generate_srt_from_audio(audio_path, language=language)
            temp_files.append(srt_path)
            
            # Step 3: Embed subtitles
            logger.info("📍 Step 3/3: Embedding subtitles...")
            success = self.embed_subtitles_in_video(
                input_video_path, srt_path, output_video_path, subtitle_style
            )
            
            if success:
                logger.info(f"🎉 Subtitle processing completed successfully!")
                logger.info(f"✅ Output saved: {output_video_path}")
            else:
                logger.error(f"❌ Subtitle processing failed")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error in subtitle processing pipeline: {e}")
            return False
            
        finally:
            # Cleanup temporary files
            if cleanup_temp_files:
                for temp_file in temp_files:
                    try:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                            logger.info(f"🗑️ Cleaned up: {os.path.basename(temp_file)}")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to cleanup {temp_file}: {e}")

    def get_available_models(self) -> list:
        """Get list of available Whisper models"""
        return ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]

    def estimate_processing_time(self, video_duration_seconds: float) -> float:
        """Estimate processing time based on video duration and model size"""
        multipliers = {
            "tiny": 0.1, "base": 0.2, "small": 0.3,
            "medium": 0.5, "large": 0.8, "large-v2": 0.8, "large-v3": 1.0
        }
        multiplier = multipliers.get(self.model_size, 0.3)
        return video_duration_seconds * multiplier
