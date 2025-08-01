"""
混合字幕生成器 - 使用Whisper時間戳 + 用戶編輯文字
Hybrid Subtitle Generator - Uses Whisper timestamps + User edited text
"""

import os
import re
import logging
import tempfile
import subprocess
from typing import List, Dict, Tuple, Optional
import whisper
from moviepy.editor import VideoFileClip

logger = logging.getLogger(__name__)

class HybridSubtitleGenerator:
    """
    混合字幕生成器
    - 使用 Whisper 分析音頻並獲取時間戳
    - 將用戶編輯的文字按比例分配到時間段
    - 生成準確的 SRT 字幕檔案
    """
    
    def __init__(self, model_size: str = "small", traditional_chinese: bool = False):
        """
        初始化混合字幕生成器
        
        Args:
            model_size: Whisper模型大小 ('tiny', 'small', 'medium', 'large')
            traditional_chinese: 是否轉換為繁體中文
        """
        self.model_size = model_size
        self.traditional_chinese = traditional_chinese
        self.model = None
        
        logger.info(f"🔧 HybridSubtitleGenerator initialized with model: {model_size}")
        
        # 初始化繁體中文轉換器（如果需要）
        if traditional_chinese:
            try:
                import opencc
                self.converter = opencc.OpenCC('s2t')
                self.use_opencc = True
                logger.info("✅ Traditional Chinese conversion enabled (OpenCC)")
            except ImportError:
                try:
                    import zhconv
                    self.zhconv = zhconv
                    self.use_opencc = False
                    logger.info("✅ Traditional Chinese conversion enabled (zhconv)")
                except ImportError:
                    self.use_opencc = None
                    logger.warning("⚠️ No Chinese conversion library available")
        else:
            self.use_opencc = None
    
    def _load_whisper_model(self):
        """延遲載入 Whisper 模型"""
        if self.model is None:
            logger.info(f"📥 Loading Whisper model: {self.model_size}")
            self.model = whisper.load_model(self.model_size)
            logger.info("✅ Whisper model loaded successfully")
    
    def generate_hybrid_subtitles(self, video_path: str, reference_texts: List[str], 
                                output_srt_path: str = None) -> str:
        """
        生成混合字幕
        
        Args:
            video_path: 視頻檔案路徑
            reference_texts: 用戶編輯的文字列表（每個元素對應一個頁面/段落）
            output_srt_path: 輸出SRT檔案路徑
        
        Returns:
            生成的SRT檔案路徑
        """
        try:
            logger.info(f"🎬 Generating hybrid subtitles for: {video_path}")
            logger.info(f"📝 Reference texts: {len(reference_texts)} segments")
            
            # 1. 從視頻提取音頻
            audio_path = self._extract_audio_from_video(video_path)
            
            # 2. 使用 Whisper 獲取時間戳
            whisper_segments = self._get_whisper_timestamps(audio_path)
            
            # 3. 將用戶文字分配到時間戳
            hybrid_segments = self._map_text_to_timestamps(whisper_segments, reference_texts)
            
            # 4. 生成 SRT 檔案
            if output_srt_path is None:
                output_srt_path = video_path.replace('.mp4', '_hybrid.srt')
            
            self._write_srt_file(hybrid_segments, output_srt_path)
            
            # 5. 清理暫存檔案
            try:
                os.unlink(audio_path)
            except Exception as e:
                logger.warning(f"⚠️ Failed to remove temp audio: {e}")
            
            logger.info(f"✅ Hybrid subtitles generated: {output_srt_path}")
            return output_srt_path
            
        except Exception as e:
            logger.error(f"❌ Error generating hybrid subtitles: {e}")
            raise
    
    def _extract_audio_from_video(self, video_path: str) -> str:
        """從視頻提取音頻"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                temp_audio_path = temp_audio.name
            
            # 使用FFmpeg提取音頻
            cmd = [
                'ffmpeg', '-i', video_path,
                '-vn', '-acodec', 'pcm_s16le',
                '-ar', '16000', '-ac', '1',
                '-y', temp_audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"❌ FFmpeg failed: {result.stderr}")
                raise Exception(f"Audio extraction failed: {result.stderr}")
            
            logger.info(f"🎵 Audio extracted to: {temp_audio_path}")
            return temp_audio_path
            
        except Exception as e:
            logger.error(f"❌ Error extracting audio: {e}")
            raise
    
    def _get_whisper_timestamps(self, audio_path: str) -> List[Dict]:
        """使用 Whisper 獲取時間戳"""
        try:
            self._load_whisper_model()
            
            logger.info("🤖 Running Whisper transcription for timestamps...")
            
            # Whisper 轉錄選項
            options = {
                "word_timestamps": True,
                "verbose": False,
                "language": "zh"  # 指定中文以提高準確性
            }
            
            result = self.model.transcribe(audio_path, **options)
            
            segments = result.get("segments", [])
            logger.info(f"⏱️ Whisper found {len(segments)} time segments")
            
            # 記錄時間戳信息
            for i, segment in enumerate(segments[:3]):  # 只記錄前3個作為示例
                logger.debug(f"   Segment {i+1}: {segment['start']:.2f}s - {segment['end']:.2f}s")
            
            return segments
            
        except Exception as e:
            logger.error(f"❌ Error getting Whisper timestamps: {e}")
            raise
    
    def _map_text_to_timestamps(self, whisper_segments: List[Dict], 
                               reference_texts: List[str]) -> List[Dict]:
        """將用戶文字分配到 Whisper 時間戳"""
        try:
            logger.info(f"🔄 Mapping {len(reference_texts)} texts to {len(whisper_segments)} timestamps")
            
            # 將所有參考文字合併並分句
            all_text = " ".join(reference_texts)
            sentences = self._split_text_into_sentences(all_text)
            
            logger.info(f"📝 Split into {len(sentences)} sentences")
            
            # 如果句子數量與時間段數量相近，直接一一對應
            if abs(len(sentences) - len(whisper_segments)) <= 2:
                return self._direct_mapping(whisper_segments, sentences)
            
            # 否則，按時間比例分配
            return self._proportional_mapping(whisper_segments, sentences)
            
        except Exception as e:
            logger.error(f"❌ Error mapping text to timestamps: {e}")
            raise
    
    def _split_text_into_sentences(self, text: str) -> List[str]:
        """將文字分割為句子"""
        # 中文句子分隔符
        sentences = re.split(r'[。！？\.\!\?；;]', text)
        # 移除空字符串並清理
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _direct_mapping(self, whisper_segments: List[Dict], 
                       sentences: List[str]) -> List[Dict]:
        """直接一一對應映射"""
        logger.info("📍 Using direct mapping")
        
        hybrid_segments = []
        min_length = min(len(whisper_segments), len(sentences))
        
        for i in range(min_length):
            segment = whisper_segments[i].copy()
            segment['text'] = self._convert_to_traditional(sentences[i])
            segment['original_text'] = segment.get('text', '')
            hybrid_segments.append(segment)
        
        # 如果還有剩餘的句子，分配到最後一個時間段
        if len(sentences) > min_length:
            remaining_text = " ".join(sentences[min_length:])
            if hybrid_segments:
                hybrid_segments[-1]['text'] += " " + self._convert_to_traditional(remaining_text)
        
        return hybrid_segments
    
    def _proportional_mapping(self, whisper_segments: List[Dict], 
                            sentences: List[str]) -> List[Dict]:
        """按比例分配映射"""
        logger.info("📊 Using proportional mapping")
        
        if not whisper_segments or not sentences:
            return []
        
        # 計算總時長
        total_duration = whisper_segments[-1]['end'] - whisper_segments[0]['start']
        
        # 計算每個句子的相對長度（字符數）
        sentence_lengths = [len(s) for s in sentences]
        total_chars = sum(sentence_lengths)
        
        hybrid_segments = []
        current_time = whisper_segments[0]['start']
        
        for i, sentence in enumerate(sentences):
            # 計算這個句子應該佔用的時間比例
            char_ratio = sentence_lengths[i] / total_chars if total_chars > 0 else 1 / len(sentences)
            sentence_duration = total_duration * char_ratio
            
            # 確保最小時長
            sentence_duration = max(sentence_duration, 1.0)
            
            start_time = current_time
            end_time = min(current_time + sentence_duration, whisper_segments[-1]['end'])
            
            # 如果是最後一個句子，延伸到最後
            if i == len(sentences) - 1:
                end_time = whisper_segments[-1]['end']
            
            hybrid_segments.append({
                'start': start_time,
                'end': end_time,
                'text': self._convert_to_traditional(sentence),
                'original_text': '',
                'mapped_method': 'proportional'
            })
            
            current_time = end_time
        
        return hybrid_segments
    
    def _convert_to_traditional(self, text: str) -> str:
        """轉換為繁體中文（如果啟用）"""
        if not self.traditional_chinese or not text:
            return text
        
        try:
            if self.use_opencc is True and hasattr(self, 'converter'):
                return self.converter.convert(text)
            elif self.use_opencc is False and hasattr(self, 'zhconv'):
                return self.zhconv.convert(text, 'zh-tw')
            else:
                return text
        except Exception as e:
            logger.warning(f"⚠️ Traditional Chinese conversion failed: {e}")
            return text
    
    def _write_srt_file(self, segments: List[Dict], output_path: str):
        """寫入 SRT 檔案"""
        srt_content = ""
        
        for i, segment in enumerate(segments, 1):
            start_time = self._format_timestamp(segment['start'])
            end_time = self._format_timestamp(segment['end'])
            text = segment['text'].strip()
            
            if text:  # 只添加非空白文字
                srt_content += f"{i}\n"
                srt_content += f"{start_time} --> {end_time}\n"
                srt_content += f"{text}\n\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        logger.info(f"📄 SRT file written with {len(segments)} segments")
    
    def _format_timestamp(self, seconds: float) -> str:
        """將秒數轉換為 SRT 時間格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

    def embed_subtitles_in_video(self, input_video_path: str, srt_path: str,
                               output_video_path: str, subtitle_style: str = "default") -> bool:
        """將字幕嵌入視頻"""
        try:
            logger.info(f"🎬 Embedding subtitles into video...")
            
            # 字幕樣式設定
            subtitle_styles = {
                "default": "FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2,Shadow=1",
                "yellow": "FontSize=24,PrimaryColour=&H00ffff,OutlineColour=&H000000,Outline=2,Shadow=1",
                "white_box": "FontSize=24,PrimaryColour=&Hffffff,BackColour=&H80000000,BorderStyle=4",
                "custom": "FontSize=26,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=3,Shadow=2"
            }
            
            style = subtitle_styles.get(subtitle_style, subtitle_styles["default"])
            
            # 使用 FFmpeg 嵌入字幕
            cmd = [
                'ffmpeg',
                '-i', input_video_path,
                '-vf', f"subtitles={srt_path}:force_style='{style}'",
                '-c:a', 'copy',
                '-y', output_video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Subtitles embedded successfully")
                return True
            else:
                logger.error(f"❌ FFmpeg failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error embedding subtitles: {e}")
            return False
