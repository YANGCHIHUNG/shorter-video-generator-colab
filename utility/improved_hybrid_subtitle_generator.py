#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
改進的混合字幕生成器 - 使用智能時間戳映射
"""

import os
import sys
import tempfile
import subprocess
import logging
import re
from typing import List, Dict, Any, Optional

# 設置日誌
logger = logging.getLogger(__name__)

class ImprovedHybridSubtitleGenerator:
    """改進的混合字幕生成器 - 智能時間戳映射"""
    
    def __init__(self, model_size: str = "small", traditional_chinese: bool = False):
        """
        初始化混合字幕生成器
        
        Args:
            model_size: Whisper 模型大小 ("tiny", "small", "medium", "large")
            traditional_chinese: 是否使用繁體中文
        """
        self.model_size = model_size
        self.traditional_chinese = traditional_chinese
        self._whisper_model = None
        
        # 導入所需模組
        try:
            import whisper
            self.whisper = whisper
            logger.info(f"✅ Whisper 模組載入成功，模型大小: {model_size}")
        except ImportError:
            logger.error("❌ 無法導入 Whisper 模組")
            raise ImportError("需要安裝 openai-whisper: pip install openai-whisper")
        
        try:
            import zhconv
            self.zhconv = zhconv
            logger.info("✅ 中文轉換模組載入成功")
        except ImportError:
            logger.warning("⚠️ 中文轉換模組未安裝，將跳過繁簡轉換")
            self.zhconv = None
        
        try:
            from fuzzywuzzy import fuzz
            self.fuzz = fuzz
            logger.info("✅ 模糊匹配模組載入成功")
        except ImportError:
            logger.warning("⚠️ 模糊匹配模組未安裝，將使用基本映射")
            self.fuzz = None
    
    def _load_whisper_model(self):
        """載入 Whisper 模型"""
        if self._whisper_model is None:
            logger.info(f"🔄 載入 Whisper 模型: {self.model_size}")
            self._whisper_model = self.whisper.load_model(self.model_size)
            logger.info("✅ Whisper 模型載入完成")
        return self._whisper_model
    
    def _extract_audio_from_video(self, video_path: str) -> str:
        """從視頻中提取音頻"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            temp_audio_path = temp_audio.name
        
        # 使用 FFmpeg 提取音頻
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le',
            '-ar', '16000', '-ac', '1',
            '-y', temp_audio_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info("✅ 音頻提取成功")
            return temp_audio_path
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 音頻提取失敗: {e.stderr}")
            raise
    
    def _transcribe_audio(self, audio_path: str) -> List[Dict[str, Any]]:
        """使用 Whisper 轉錄音頻並獲取詳細時間戳"""
        model = self._load_whisper_model()
        
        logger.info("🎯 開始音頻轉錄...")
        result = model.transcribe(
            audio_path,
            language='zh',  # 指定中文
            word_timestamps=True,
            verbose=False
        )
        
        segments = result.get('segments', [])
        logger.info(f"✅ 轉錄完成，共 {len(segments)} 個片段")
        
        # 記錄 Whisper 轉錄結果用於調試
        for i, segment in enumerate(segments[:3]):  # 只記錄前3個
            logger.debug(f"  Whisper 片段 {i+1}: {segment['start']:.1f}s-{segment['end']:.1f}s: {segment['text']}")
        
        return segments
    
    def _split_text_into_sentences(self, text: str) -> List[str]:
        """將文字分割成句子"""
        # 中文句號、問號、感嘆號作為分句標準
        sentences = re.split(r'[。！？\n]+', text.strip())
        # 移除空字符串並清理空格
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _smart_map_text_to_segments(self, whisper_segments: List[Dict], reference_texts: List[str]) -> List[Dict]:
        """智能映射用戶文字到 Whisper 時間片段"""
        mapped_segments = []
        
        if not whisper_segments:
            logger.warning("⚠️ 沒有 Whisper 片段可供映射")
            return mapped_segments
        
        logger.info(f"🧠 開始智能映射：{len(reference_texts)} 個用戶文字 → {len(whisper_segments)} 個 Whisper 片段")
        
        # 將所有用戶文字分割成句子
        all_sentences = []
        text_to_page = {}  # 記錄每個句子屬於哪一頁
        
        for page_idx, page_text in enumerate(reference_texts):
            sentences = self._split_text_into_sentences(page_text)
            for sentence in sentences:
                all_sentences.append(sentence)
                text_to_page[sentence] = page_idx
        
        logger.info(f"📝 總共分割出 {len(all_sentences)} 個句子")
        
        # 策略1: 如果句子數量與 Whisper 片段數量相近，嘗試一對一映射
        if abs(len(all_sentences) - len(whisper_segments)) <= 2:
            logger.info("🎯 使用一對一映射策略")
            return self._one_to_one_mapping(whisper_segments, all_sentences)
        
        # 策略2: 如果用戶頁面數與 Whisper 片段數相近，按頁面映射
        elif abs(len(reference_texts) - len(whisper_segments)) <= 1:
            logger.info("📄 使用頁面對片段映射策略")
            return self._page_to_segment_mapping(whisper_segments, reference_texts)
        
        # 策略3: 比例分配映射
        else:
            logger.info("⚖️ 使用比例分配映射策略")
            return self._proportional_mapping(whisper_segments, all_sentences)
    
    def _one_to_one_mapping(self, whisper_segments: List[Dict], sentences: List[str]) -> List[Dict]:
        """一對一映射策略"""
        mapped_segments = []
        
        for i in range(max(len(whisper_segments), len(sentences))):
            if i < len(whisper_segments):
                start_time = whisper_segments[i]["start"]
                end_time = whisper_segments[i]["end"]
            else:
                # 如果句子比片段多，延續最後一個片段的時間
                last_segment = whisper_segments[-1]
                duration = last_segment["end"] - last_segment["start"]
                start_time = last_segment["end"] + (i - len(whisper_segments)) * duration
                end_time = start_time + duration
            
            if i < len(sentences):
                text = self._convert_chinese(sentences[i])
            else:
                # 如果片段比句子多，使用最後一個句子
                text = self._convert_chinese(sentences[-1]) if sentences else "無音頻內容"
            
            mapped_segments.append({
                "start": start_time,
                "end": end_time,
                "text": text
            })
        
        return mapped_segments
    
    def _page_to_segment_mapping(self, whisper_segments: List[Dict], reference_texts: List[str]) -> List[Dict]:
        """頁面對片段映射策略"""
        mapped_segments = []
        
        for i in range(max(len(whisper_segments), len(reference_texts))):
            if i < len(whisper_segments):
                start_time = whisper_segments[i]["start"]
                end_time = whisper_segments[i]["end"]
            else:
                # 如果頁面比片段多，延續時間
                last_segment = whisper_segments[-1]
                duration = (last_segment["end"] - whisper_segments[0]["start"]) / len(reference_texts)
                start_time = whisper_segments[0]["start"] + i * duration
                end_time = start_time + duration
            
            if i < len(reference_texts):
                text = self._convert_chinese(reference_texts[i])
            else:
                # 如果片段比頁面多，使用最後一頁
                text = self._convert_chinese(reference_texts[-1]) if reference_texts else "無音頻內容"
            
            mapped_segments.append({
                "start": start_time,
                "end": end_time,
                "text": text
            })
        
        return mapped_segments
    
    def _proportional_mapping(self, whisper_segments: List[Dict], sentences: List[str]) -> List[Dict]:
        """比例分配映射策略"""
        mapped_segments = []
        
        total_duration = whisper_segments[-1]["end"] - whisper_segments[0]["start"]
        sentence_duration = total_duration / len(sentences) if sentences else 0
        
        for i, sentence in enumerate(sentences):
            start_time = whisper_segments[0]["start"] + (i * sentence_duration)
            end_time = start_time + sentence_duration
            
            # 確保最後一個句子的結束時間與 Whisper 一致
            if i == len(sentences) - 1:
                end_time = whisper_segments[-1]["end"]
            
            text = self._convert_chinese(sentence)
            
            mapped_segments.append({
                "start": start_time,
                "end": end_time,
                "text": text
            })
        
        return mapped_segments
    
    def _convert_chinese(self, text: str) -> str:
        """繁簡中文轉換"""
        if self.traditional_chinese and self.zhconv:
            try:
                return self.zhconv.convert(text, 'zh-tw')
            except Exception as e:
                logger.warning(f"⚠️ 中文轉換失敗: {e}")
                return text
        return text
    
    def _generate_srt_content(self, segments: List[Dict]) -> str:
        """生成 SRT 字幕內容"""
        srt_content = ""
        
        for i, segment in enumerate(segments, 1):
            start_time = self._format_time(segment["start"])
            end_time = self._format_time(segment["end"])
            text = segment["text"]
            
            srt_content += f"{i}\n"
            srt_content += f"{start_time} --> {end_time}\n"
            srt_content += f"{text}\n\n"
        
        return srt_content
    
    def _format_time(self, seconds: float) -> str:
        """將秒數轉換為 SRT 時間格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds_remainder = seconds % 60
        milliseconds = int((seconds_remainder % 1) * 1000)
        seconds_int = int(seconds_remainder)
        
        return f"{hours:02d}:{minutes:02d}:{seconds_int:02d},{milliseconds:03d}"
    
    def generate_hybrid_subtitles(self, video_path: str, reference_texts: List[str]) -> str:
        """
        生成改進的混合字幕
        
        Args:
            video_path: 視頻文件路徑
            reference_texts: 用戶提供的參考文字列表（每個元素代表一頁）
            
        Returns:
            SRT 字幕文件路徑
        """
        logger.info("🚀 開始生成改進的混合字幕...")
        logger.info(f"📖 用戶提供了 {len(reference_texts)} 頁文字")
        
        # 1. 提取音頻
        audio_path = self._extract_audio_from_video(video_path)
        
        try:
            # 2. 使用 Whisper 轉錄獲取時間戳
            whisper_segments = self._transcribe_audio(audio_path)
            
            # 3. 智能映射用戶文字到時間片段
            mapped_segments = self._smart_map_text_to_segments(whisper_segments, reference_texts)
            
            # 4. 生成 SRT 內容
            srt_content = self._generate_srt_content(mapped_segments)
            
            # 5. 保存 SRT 文件
            srt_path = video_path.replace('.mp4', '_improved_hybrid.srt')
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            logger.info(f"✅ 改進混合字幕生成完成: {srt_path}")
            logger.info(f"📊 最終生成 {len(mapped_segments)} 個字幕片段")
            
            return srt_path
            
        finally:
            # 清理暫存音頻文件
            try:
                os.unlink(audio_path)
                logger.info("🧹 暫存音頻文件已清理")
            except Exception as e:
                logger.warning(f"⚠️ 清理暫存文件失敗: {e}")
    
    def embed_subtitles_in_video(self, 
                                input_video_path: str, 
                                srt_path: str, 
                                output_video_path: str,
                                subtitle_style: str = "default") -> bool:
        """
        使用 FFmpeg 將字幕嵌入視頻
        
        Args:
            input_video_path: 輸入視頻路徑
            srt_path: SRT 字幕文件路徑
            output_video_path: 輸出視頻路徑
            subtitle_style: 字幕樣式
            
        Returns:
            成功返回 True，失敗返回 False
        """
        logger.info("🎬 開始將改進字幕嵌入視頻...")
        
        # 字幕樣式設定
        style_options = {
            "default": "FontSize=24,FontName=Microsoft YaHei,PrimaryColour=&Hffffff,BackColour=&H80000000,BorderStyle=1,Outline=1,Shadow=1",
            "large": "FontSize=32,FontName=Microsoft YaHei,PrimaryColour=&Hffffff,BackColour=&H80000000,BorderStyle=1,Outline=1,Shadow=1",
            "bold": "FontSize=28,FontName=Microsoft YaHei,Bold=1,PrimaryColour=&Hffffff,BackColour=&H80000000,BorderStyle=1,Outline=2,Shadow=1"
        }
        
        style = style_options.get(subtitle_style, style_options["default"])
        
        # FFmpeg 命令
        cmd = [
            'ffmpeg',
            '-i', input_video_path,
            '-vf', f"subtitles={srt_path}:force_style='{style}'",
            '-c:a', 'copy',
            '-y', output_video_path
        ]
        
        try:
            logger.info("🔄 執行 FFmpeg 字幕嵌入...")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info("✅ 改進字幕嵌入成功")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 字幕嵌入失敗: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"❌ 字幕嵌入過程發生錯誤: {e}")
            return False
