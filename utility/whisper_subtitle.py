"""
Whisper-based subtitle generation and embedding utilities
"""

import os
import subprocess
import tempfile
import logging
from typing import Optional, List, Dict, Any
import json

logger = logging.getLogger(__name__)

class WhisperSubtitleGenerator:
    """Generate and embed subtitles using Whisper and FFmpeg"""
    
    def __init__(self):
        self.model = None
        self.model_size = "base"  # Balance between speed and accuracy
    
    def load_whisper_model(self, model_size: str = "base"):
        """Load Whisper model for transcription"""
        try:
            import whisper
            logger.info(f"🤖 Loading Whisper model: {model_size}")
            self.model = whisper.load_model(model_size)
            self.model_size = model_size
            logger.info("✅ Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load Whisper model: {e}")
            raise
    
    def extract_audio_from_video(self, video_path: str, audio_path: str) -> bool:
        """Extract audio from video using FFmpeg"""
        try:
            logger.info(f"🎵 Extracting audio from video: {video_path}")
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # Uncompressed audio for better Whisper results
                '-ar', '16000',  # 16kHz sample rate (Whisper's preferred)
                '-ac', '1',  # Mono
                '-y',  # Overwrite output file
                audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Audio extracted successfully: {audio_path}")
                return True
            else:
                logger.error(f"❌ FFmpeg audio extraction failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error extracting audio: {e}")
            return False
    
    def generate_srt_from_audio(self, audio_path: str, srt_path: str, language: str = "auto") -> bool:
        """Generate SRT subtitle file from audio using Whisper"""
        try:
            if not self.model:
                self.load_whisper_model(self.model_size)
            
            logger.info(f"🎯 Transcribing audio with Whisper...")
            
            # Transcribe with word-level timestamps
            result = self.model.transcribe(
                audio_path,
                language=language if language != "auto" else None,
                word_timestamps=True,
                verbose=False
            )
            
            # Generate SRT content
            srt_content = self._create_srt_from_whisper_result(result)
            
            # Save SRT file
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            logger.info(f"✅ SRT subtitles generated: {srt_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error generating SRT: {e}")
            return False
    
    def _create_srt_from_whisper_result(self, result: Dict[str, Any]) -> str:
        """Convert Whisper transcription result to SRT format"""
        srt_content = ""
        subtitle_index = 1
        
        for segment in result['segments']:
            start_time = self._seconds_to_srt_time(segment['start'])
            end_time = self._seconds_to_srt_time(segment['end'])
            text = segment['text'].strip()
            
            if text:  # Only add non-empty segments
                srt_content += f"{subtitle_index}\n"
                srt_content += f"{start_time} --> {end_time}\n"
                srt_content += f"{text}\n\n"
                subtitle_index += 1
        
        return srt_content
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds_remainder = seconds % 60
        seconds_int = int(seconds_remainder)
        milliseconds = int((seconds_remainder - seconds_int) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{seconds_int:02d},{milliseconds:03d}"
    
    def embed_subtitles_in_video(self, input_video_path: str, srt_path: str, 
                               output_video_path: str, subtitle_style: str = "default") -> bool:
        """Embed SRT subtitles into video using FFmpeg"""
        try:
            logger.info(f"🎬 Embedding subtitles into video...")
            
            # Define subtitle styles
            styles = {
                "default": "FontName=Arial,FontSize=16,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2",
                "yellow": "FontName=Arial,FontSize=16,PrimaryColour=&H00ffff,OutlineColour=&H000000,Outline=2",
                "white_box": "FontName=Arial,FontSize=16,PrimaryColour=&Hffffff,BackColour=&H000000,BorderStyle=4",
                "custom": "FontName=Arial,FontSize=18,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Bold=1"
            }
            
            style = styles.get(subtitle_style, styles["default"])
            
            cmd = [
                'ffmpeg', '-i', input_video_path,
                '-vf', f'subtitles={srt_path}:force_style=\'{style}\'',
                '-c:a', 'copy',  # Copy audio without re-encoding
                '-y',  # Overwrite output file
                output_video_path
            ]
            
            logger.info(f"🔧 FFmpeg command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Subtitles embedded successfully: {output_video_path}")
                return True
            else:
                logger.error(f"❌ FFmpeg subtitle embedding failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error embedding subtitles: {e}")
            return False
    
    def process_video_with_subtitles(self, input_video_path: str, output_video_path: str,
                                   subtitle_style: str = "default", language: str = "auto") -> bool:
        """Complete pipeline: extract audio, generate SRT, embed subtitles"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Temporary file paths
                temp_audio = os.path.join(temp_dir, "audio.wav")
                temp_srt = os.path.join(temp_dir, "subtitles.srt")
                
                # Step 1: Extract audio
                if not self.extract_audio_from_video(input_video_path, temp_audio):
                    return False
                
                # Step 2: Generate SRT
                if not self.generate_srt_from_audio(temp_audio, temp_srt, language):
                    return False
                
                # Step 3: Embed subtitles
                if not self.embed_subtitles_in_video(input_video_path, temp_srt, 
                                                   output_video_path, subtitle_style):
                    return False
                
                logger.info("✅ Video with subtitles processed successfully!")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error in subtitle processing pipeline: {e}")
            return False

def check_whisper_dependencies() -> Dict[str, bool]:
    """Check if required dependencies are available"""
    dependencies = {}
    
    # Check FFmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
        dependencies['ffmpeg'] = result.returncode == 0
    except FileNotFoundError:
        dependencies['ffmpeg'] = False
    
    # Check Whisper
    try:
        import whisper
        dependencies['whisper'] = True
    except ImportError:
        dependencies['whisper'] = False
    
    return dependencies

# Create alias for backward compatibility
SubtitleGenerator = WhisperSubtitleGenerator
check_dependencies = check_whisper_dependencies

if __name__ == "__main__":
    # Test the subtitle generator
    deps = check_dependencies()
    print("Dependencies check:")
    for dep, available in deps.items():
        status = "✅" if available else "❌"
        print(f"{status} {dep}: {'Available' if available else 'Missing'}")
