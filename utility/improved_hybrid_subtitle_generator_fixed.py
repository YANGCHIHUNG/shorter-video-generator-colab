#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
改進的混合字幕生成器 - 支援字幕長度控制和智能時間戳映射
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
    """改進的混合字幕生成器 - 智能時間戳映射和字幕長度控制"""
    
    def __init__(self, model_size: str = "small", traditional_chinese: bool = False, subtitle_length_mode: str = "auto"):
        """
        初始化混合字幕生成器
        
        Args:
            model_size: Whisper 模型大小 ("tiny", "small", "medium", "large")
            traditional_chinese: 是否使用繁體中文
            subtitle_length_mode: 字幕長度控制模式 ('auto', 'compact', 'standard', 'relaxed')
        """
        self.model_size = model_size
        self.traditional_chinese = traditional_chinese
        self.subtitle_length_mode = subtitle_length_mode
        self._whisper_model = None
        
        # 配置字幕長度參數
        self._configure_length_parameters()
        
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
            import difflib
            self.difflib = difflib
            logger.info("✅ 文字比對模組載入成功")
        except ImportError:
            logger.warning("⚠️ 文字比對模組未安裝")
            self.difflib = None
        
        try:
            from fuzzywuzzy import fuzz
            self.fuzz = fuzz
            logger.info("✅ 模糊匹配模組載入成功")
        except ImportError:
            logger.warning("⚠️ 模糊匹配模組未安裝，將使用基本映射")
            self.fuzz = None
    
    def _configure_length_parameters(self):
        """根據字幕長度模式配置參數"""
        length_configs = {
            'compact': {
                'max_chars_per_line': 12,
                'max_lines': 2,
                'min_display_time': 1.8
            },
            'standard': {
                'max_chars_per_line': 15,
                'max_lines': 2,
                'min_display_time': 1.5
            },
            'relaxed': {
                'max_chars_per_line': 18,
                'max_lines': 2,
                'min_display_time': 1.2
            },
            'auto': {
                'max_chars_per_line': 15,  # 預設值
                'max_lines': 2,
                'min_display_time': 1.5
            }
        }
        
        config = length_configs.get(self.subtitle_length_mode, length_configs['auto'])
        self.max_chars_per_line = config['max_chars_per_line']
        self.max_lines = config['max_lines']
        self.min_display_time = config['min_display_time']
        self.max_chars_total = self.max_chars_per_line * self.max_lines
        
        logger.info(f"📏 字幕長度配置: {self.subtitle_length_mode} - "
                   f"每行{self.max_chars_per_line}字，最多{self.max_lines}行")
    
    def get_whisper_model(self):
        """獲取 Whisper 模型實例"""
        if self._whisper_model is None:
            try:
                logger.info(f"🔄 正在載入 Whisper 模型: {self.model_size}")
                self._whisper_model = self.whisper.load_model(self.model_size)
                logger.info(f"✅ Whisper 模型載入完成: {self.model_size}")
            except Exception as e:
                logger.error(f"❌ 載入 Whisper 模型失敗: {e}")
                raise e
        return self._whisper_model
    
    def transcribe_audio(self, audio_path: str) -> List[Dict]:
        """使用 Whisper 轉錄音頻並獲取時間戳"""
        try:
            model = self.get_whisper_model()
            logger.info(f"🎙️ 開始轉錄音頻: {audio_path}")
            
            result = model.transcribe(
                audio_path,
                word_timestamps=True,
                verbose=False
            )
            
            segments = result.get("segments", [])
            logger.info(f"✅ 音頻轉錄完成，獲得 {len(segments)} 個片段")
            
            return segments
            
        except Exception as e:
            logger.error(f"❌ 音頻轉錄失敗: {e}")
            raise e
    
    def _smart_split_text_into_sentences(self, text: str) -> List[str]:
        """智能中文分句"""
        if not text:
            return []
        
        # 中文句號、感嘆號、問號等
        sentence_endings = r'[。！？；]'
        
        # 先按主要標點分割
        sentences = re.split(sentence_endings, text)
        
        # 清理並重組句子（保留標點）
        result_sentences = []
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if sentence:
                # 重新添加標點（除了最後一個空字符串）
                if i < len(sentences) - 1:
                    # 查找原文中對應的標點
                    original_pos = sum(len(sentences[j]) for j in range(i + 1)) + i
                    if original_pos < len(text):
                        punct = text[original_pos]
                        sentence += punct
                result_sentences.append(sentence)
        
        # 如果分句失敗，按逗號分割
        if len(result_sentences) <= 1:
            sentences = text.split('，')
            result_sentences = [s.strip() for s in sentences if s.strip()]
        
        logger.info(f"📝 文字分句完成: {len(result_sentences)} 個句子")
        return result_sentences
    
    def _convert_chinese(self, text: str) -> str:
        """中文繁簡轉換"""
        if not self.traditional_chinese or not self.zhconv:
            return text
        
        try:
            return self.zhconv.convert(text, 'zh-tw')
        except Exception as e:
            logger.warning(f"⚠️ 中文轉換失敗: {e}")
            return text
        
    def _generate_srt_content(self, segments: List[Dict]) -> str:
        """生成 SRT 字幕內容（支援長字幕切分）"""
        srt_content = ""
        subtitle_index = 1
        
        for segment in segments:
            start_time = segment["start"]
            end_time = segment["end"]
            text = segment["text"]
            
            # 切分過長的字幕
            split_subtitles = self._split_long_subtitle(text, start_time, end_time)
            
            for sub_segment in split_subtitles:
                srt_start_time = self._format_time(sub_segment["start"])
                srt_end_time = self._format_time(sub_segment["end"])
                sub_text = sub_segment["text"]
                
                srt_content += f"{subtitle_index}\n"
                srt_content += f"{srt_start_time} --> {srt_end_time}\n"
                srt_content += f"{sub_text}\n\n"
                subtitle_index += 1
        
        return srt_content
    
    def _split_long_subtitle(self, text: str, start_time: float, end_time: float) -> List[Dict]:
        """
        切分過長的字幕
        
        Args:
            text: 原始字幕文字
            start_time: 開始時間
            end_time: 結束時間
            
        Returns:
            切分後的字幕片段列表
        """
        # 使用配置的字幕顯示參數
        max_chars_per_line = self.max_chars_per_line
        max_lines = self.max_lines
        max_chars_total = self.max_chars_total
        min_display_time = self.min_display_time
        
        # 如果文字不超過限制，直接返回
        if len(text) <= max_chars_total:
            formatted_text = self._format_subtitle_lines(text, max_chars_per_line)
            return [{
                "start": start_time,
                "end": end_time,
                "text": formatted_text
            }]
        
        # 切分長文字
        segments = []
        total_duration = end_time - start_time
        
        # 智能分句：優先按標點符號切分
        sentences = self._smart_split_by_punctuation(text, max_chars_total)
        
        # 計算每個分段的時間
        total_chars = sum(len(sentence) for sentence in sentences)
        current_time = start_time
        
        for i, sentence in enumerate(sentences):
            # 根據字元數比例分配時間
            if total_chars > 0:
                segment_duration = (len(sentence) / total_chars) * total_duration
            else:
                segment_duration = total_duration / len(sentences)
            
            # 確保最小顯示時間
            segment_duration = max(segment_duration, min_display_time)
            
            # 計算結束時間
            segment_end_time = current_time + segment_duration
            
            # 最後一個片段對齊原始結束時間
            if i == len(sentences) - 1:
                segment_end_time = end_time
            
            # 進一步切分過長的句子（如果單句仍然太長）
            if len(sentence) > max_chars_total:
                sub_segments = self._force_split_long_sentence(
                    sentence, current_time, segment_end_time, max_chars_total
                )
                segments.extend(sub_segments)
                current_time = sub_segments[-1]["end"]
            else:
                # 格式化為雙行顯示
                formatted_text = self._format_subtitle_lines(sentence, max_chars_per_line)
                segments.append({
                    "start": current_time,
                    "end": segment_end_time,
                    "text": formatted_text
                })
                current_time = segment_end_time
        
        return segments
    
    def _smart_split_by_punctuation(self, text: str, max_chars: int) -> List[str]:
        """根據標點符號智能切分文字"""
        # 中文標點符號
        punctuation_marks = ['。', '！', '？', '；', '，', '、', '：']
        
        sentences = []
        current_sentence = ""
        
        for char in text:
            current_sentence += char
            
            # 遇到標點符號且長度適中時切分
            if char in punctuation_marks and len(current_sentence.strip()) > 0:
                if len(current_sentence) <= max_chars:
                    sentences.append(current_sentence.strip())
                    current_sentence = ""
                # 如果加上標點後仍然太長，先切分前面的部分
                elif len(current_sentence) > max_chars:
                    # 回退到標點前
                    pre_punct = current_sentence[:-1].strip()
                    if pre_punct:
                        sentences.append(pre_punct)
                    current_sentence = char  # 保留標點符號
        
        # 處理剩餘文字
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        # 合併過短的片段
        return self._merge_short_segments(sentences, max_chars)
    
    def _merge_short_segments(self, sentences: List[str], max_chars: int) -> List[str]:
        """合併過短的片段"""
        merged = []
        current = ""
        
        for sentence in sentences:
            # 如果合併後不超過限制，則合併
            if len(current + sentence) <= max_chars:
                current += sentence
            else:
                # 保存當前片段，開始新片段
                if current:
                    merged.append(current)
                current = sentence
        
        # 添加最後一個片段
        if current:
            merged.append(current)
        
        return merged
    
    def _force_split_long_sentence(self, sentence: str, start_time: float, end_time: float, max_chars: int) -> List[Dict]:
        """強制切分過長的句子"""
        segments = []
        total_duration = end_time - start_time
        
        # 按最大字元數強制切分
        parts = []
        for i in range(0, len(sentence), max_chars):
            parts.append(sentence[i:i + max_chars])
        
        # 分配時間
        current_time = start_time
        for i, part in enumerate(parts):
            # 根據字元數比例分配時間
            part_duration = (len(part) / len(sentence)) * total_duration
            part_end_time = current_time + part_duration
            
            # 最後一個片段對齊結束時間
            if i == len(parts) - 1:
                part_end_time = end_time
            
            # 格式化為雙行顯示
            formatted_text = self._format_subtitle_lines(part, self.max_chars_per_line)
            segments.append({
                "start": current_time,
                "end": part_end_time,
                "text": formatted_text
            })
            
            current_time = part_end_time
        
        return segments
    
    def _format_subtitle_lines(self, text: str, max_chars_per_line: int) -> str:
        """將文字格式化為適合的行數"""
        if len(text) <= max_chars_per_line:
            return text
        
        # 嘗試在合適的位置斷行
        words = list(text)  # 中文按字元處理
        lines = []
        current_line = ""
        
        for char in words:
            if len(current_line + char) <= max_chars_per_line:
                current_line += char
            else:
                if current_line:
                    lines.append(current_line)
                current_line = char
        
        # 添加最後一行
        if current_line:
            lines.append(current_line)
        
        # 最多兩行，如果超過則合併
        if len(lines) > 2:
            # 重新分配到兩行
            half_chars = len(text) // 2
            line1 = text[:half_chars]
            line2 = text[half_chars:]
            return f"{line1}\n{line2}"
        else:
            return "\n".join(lines)
    
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
        try:
            logger.info(f"🎬 開始生成混合字幕，視頻: {video_path}")
            logger.info(f"📄 參考文字頁數: {len(reference_texts)}")
            
            # 從視頻提取音頻
            audio_path = self._extract_audio_from_video(video_path)
            
            # 使用 Whisper 轉錄音頻獲取時間戳
            whisper_segments = self.transcribe_audio(audio_path)
            
            # 映射用戶文字到 Whisper 時間片段
            mapped_segments = self._map_text_to_segments(whisper_segments, reference_texts)
            
            # 生成 SRT 內容（包含長字幕切分）
            srt_content = self._generate_srt_content(mapped_segments)
            
            # 保存 SRT 文件
            srt_path = video_path.replace('.mp4', '_hybrid.srt')
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            logger.info(f"✅ 混合字幕生成完成: {srt_path}")
            
            # 清理臨時音頻文件
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            return srt_path
            
        except Exception as e:
            logger.error(f"❌ 混合字幕生成失敗: {e}")
            raise e
    
    def _extract_audio_from_video(self, video_path: str) -> str:
        """從視頻中提取音頻"""
        try:
            # 創建臨時音頻文件
            audio_path = video_path.replace('.mp4', '_temp_audio.wav')
            
            # 使用 ffmpeg 提取音頻
            cmd = [
                'ffmpeg', '-i', video_path,
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                '-y', audio_path
            ]
            
            logger.info(f"🎵 正在提取音頻: {video_path} -> {audio_path}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg 提取音頻失敗: {result.stderr}")
            
            logger.info(f"✅ 音頻提取完成: {audio_path}")
            return audio_path
            
        except Exception as e:
            logger.error(f"❌ 音頻提取失敗: {e}")
            raise e
    
    def _map_text_to_segments(self, whisper_segments: List[Dict], reference_texts: List[str]) -> List[Dict]:
        """映射用戶文字到 Whisper 時間片段"""
        mapped_segments = []
        
        if not whisper_segments or not reference_texts:
            return mapped_segments
        
        logger.info(f"🧠 開始映射：{len(reference_texts)} 個用戶文字 → {len(whisper_segments)} 個 Whisper 片段")
        
        # 將所有用戶文字分割成句子
        all_sentences = []
        for page_text in reference_texts:
            sentences = self._smart_split_text_into_sentences(page_text)
            all_sentences.extend(sentences)
        
        logger.info(f"📝 總共分割出 {len(all_sentences)} 個句子")
        
        # 智能映射策略
        if len(all_sentences) == len(whisper_segments):
            # 一對一映射
            for i, sentence in enumerate(all_sentences):
                whisper_seg = whisper_segments[i]
                text = self._convert_chinese(sentence)
                
                mapped_segments.append({
                    "start": whisper_seg["start"],
                    "end": whisper_seg["end"],
                    "text": text
                })
        else:
            # 比例分配映射
            total_duration = whisper_segments[-1]["end"] - whisper_segments[0]["start"]
            sentence_duration = total_duration / len(all_sentences) if all_sentences else 0
            
            for i, sentence in enumerate(all_sentences):
                start_time = whisper_segments[0]["start"] + (i * sentence_duration)
                end_time = start_time + sentence_duration
                
                # 確保最後一個句子的結束時間與 Whisper 一致
                if i == len(all_sentences) - 1:
                    end_time = whisper_segments[-1]["end"]
                
                text = self._convert_chinese(sentence)
                
                mapped_segments.append({
                    "start": start_time,
                    "end": end_time,
                    "text": text
                })
        
        logger.info(f"✅ 映射完成，生成 {len(mapped_segments)} 個字幕片段")
        return mapped_segments
    
    def embed_subtitles_in_video(self, input_video_path: str, srt_path: str, output_video_path: str, style: str = "default") -> bool:
        """將字幕嵌入視頻"""
        try:
            logger.info(f"🎬 開始嵌入字幕: {input_video_path}")
            
            # 字幕樣式配置
            style_configs = {
                "default": "force_style='FontName=Microsoft YaHei,FontSize=24,PrimaryColour=&Hffffff,SecondaryColour=&Hffffff,OutlineColour=&H0,BackColour=&H80000000,Bold=1,Italic=0,Underline=0,StrikeOut=0,ScaleX=100,ScaleY=100,Spacing=0,Angle=0,BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginL=10,MarginR=10,MarginV=10'",
                "yellow": "force_style='FontName=Microsoft YaHei,FontSize=24,PrimaryColour=&H00ffff,SecondaryColour=&H00ffff,OutlineColour=&H0,BackColour=&H80000000,Bold=1,Italic=0,Underline=0,StrikeOut=0,ScaleX=100,ScaleY=100,Spacing=0,Angle=0,BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginL=10,MarginR=10,MarginV=10'",
                "white_box": "force_style='FontName=Microsoft YaHei,FontSize=24,PrimaryColour=&Hffffff,SecondaryColour=&Hffffff,OutlineColour=&H0,BackColour=&H80000000,Bold=1,Italic=0,Underline=0,StrikeOut=0,ScaleX=100,ScaleY=100,Spacing=0,Angle=0,BorderStyle=3,Outline=1,Shadow=0,Alignment=2,MarginL=10,MarginR=10,MarginV=10'"
            }
            
            style_option = style_configs.get(style, style_configs["default"])
            
            cmd = [
                'ffmpeg',
                '-i', input_video_path,
                '-vf', f"subtitles={srt_path}:{style_option}",
                '-c:a', 'copy',
                '-y', output_video_path
            ]
            
            logger.info(f"🔧 執行 FFmpeg 命令嵌入字幕")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"❌ FFmpeg 嵌入字幕失敗: {result.stderr}")
                return False
            
            logger.info(f"✅ 字幕嵌入完成: {output_video_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 字幕嵌入失敗: {e}")
            return False
