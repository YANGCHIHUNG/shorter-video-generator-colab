#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基於語速計算的字幕生成器 - 支援標點符號斷句和單行顯示
"""

import os
import sys
import tempfile
import subprocess
import logging
import re
import platform
from typing import List, Dict, Any, Optional

# 設置日誌
logger = logging.getLogger(__name__)

def get_available_chinese_font():
    """
    跨平台檢測可用的中文字體
    Returns:
        str: 字體文件路徑或字體名稱，如果找不到則返回 None
    """
    system = platform.system()
    
    if system == "Linux":
        # Linux/Colab 環境 - 檢查 Noto 字體
        linux_fonts = [
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        ]
        for font_path in linux_fonts:
            if os.path.exists(font_path):
                logger.info(f"🔤 找到 Linux 字體: {font_path}")
                return font_path
        logger.warning("⚠️ Linux 環境未找到理想中文字體，使用系統默認")
        return None
        
    elif system == "Windows":
        # Windows 環境
        windows_fonts = [
            "C:/Windows/Fonts/msyh.ttc",  # Microsoft YaHei
            "C:/Windows/Fonts/simhei.ttf",  # SimHei
            "C:/Windows/Fonts/simsun.ttc"   # SimSun
        ]
        for font_path in windows_fonts:
            if os.path.exists(font_path):
                logger.info(f"🔤 找到 Windows 字體: {font_path}")
                return font_path
        return "Microsoft YaHei"  # 字體名稱
        
    elif system == "Darwin":  # macOS
        # macOS 環境
        macos_fonts = [
            "/System/Library/Fonts/PingFang.ttc",
            "/Library/Fonts/Arial Unicode MS.ttf",
            "/System/Library/Fonts/STHeiti Light.ttc"
        ]
        for font_path in macos_fonts:
            if os.path.exists(font_path):
                logger.info(f"🔤 找到 macOS 字體: {font_path}")
                return font_path
        return "PingFang SC"  # 字體名稱
    
    logger.warning(f"⚠️ 未識別的系統: {system}，使用默認字體")
    return None

class SpeechRateSubtitleGenerator:
    """基於語速計算的字幕生成器 - 標點符號斷句"""
    
    def __init__(self, traditional_chinese: bool = False, chars_per_line: int = 25):
        """
        初始化字幕生成器 - 單行標點符號斷句模式
        
        Args:
            traditional_chinese: 是否使用繁體中文
            chars_per_line: 每行最大字數（單行模式）
        """
        self.traditional_chinese = traditional_chinese
        
        # 設置字幕顯示參數 - 強制單行顯示
        self.chars_per_line = chars_per_line
        self.max_lines = 1  # 強制只有一行
        self.min_display_time = 1.5  # 最小顯示時間（秒）
        
        # 字幕生成器配置
        logger.info(f"📏 字幕生成器配置: 語速計算 + 標點符號斷句 - 每行{self.chars_per_line}字，單行顯示")
        
        # 中文轉換模組（可選）
        try:
            import zhconv
            self.zhconv = zhconv
            logger.info("✅ 中文轉換模組載入成功")
        except ImportError:
            logger.warning("⚠️ 中文轉換模組未安裝，將跳過繁簡轉換")
            self.zhconv = None
    
    
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
        max_chars_per_line = self.chars_per_line
        max_lines = self.max_lines
        max_chars_total = max_chars_per_line * max_lines
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
            
            # 確保時間不會倒退
            if segment_end_time <= current_time:
                segment_end_time = current_time + min_display_time
            
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
        """基於標點符號的智能斷句機制"""
        
        # 定義中文標點符號的優先順序（優先在這些符號處斷句）
        primary_punctuation = ['。', '！', '？']  # 強斷句標點
        secondary_punctuation = ['；', '：']      # 中等斷句標點  
        tertiary_punctuation = ['，', '、']       # 弱斷句標點
        
        sentences = []
        current_sentence = ""
        
        i = 0
        while i < len(text):
            char = text[i]
            current_sentence += char
            
            # 檢查是否遇到標點符號
            if char in primary_punctuation + secondary_punctuation + tertiary_punctuation:
                # 如果當前句子長度適中，在此處斷句
                if 5 <= len(current_sentence.strip()) <= max_chars:
                    sentences.append(current_sentence.strip())
                    current_sentence = ""
                    i += 1
                    continue
                # 如果當前句子太長，需要在前面找合適的斷點
                elif len(current_sentence.strip()) > max_chars:
                    # 在當前句子中找最佳斷點
                    best_split = self._find_best_split_point(current_sentence[:-1], max_chars)
                    if best_split:
                        sentences.append(best_split.strip())
                        current_sentence = current_sentence[len(best_split):].strip()
                    else:
                        # 如果找不到合適斷點，強制斷句
                        split_point = max_chars
                        sentences.append(current_sentence[:split_point].strip())
                        current_sentence = current_sentence[split_point:].strip()
            
            # 如果當前句子已經太長，即使沒有標點也要斷句
            elif len(current_sentence) > max_chars * 1.5:  # 給一些緩衝空間
                # 嘗試找到合適的斷點
                best_split = self._find_best_split_point(current_sentence, max_chars)
                if best_split:
                    sentences.append(best_split.strip())
                    current_sentence = current_sentence[len(best_split):].strip()
                else:
                    # 強制斷句
                    sentences.append(current_sentence[:max_chars].strip())
                    current_sentence = current_sentence[max_chars:].strip()
                continue
            
            i += 1
        
        # 處理剩餘文字
        if current_sentence.strip():
            # 如果剩餘文字太長，再次切分
            if len(current_sentence.strip()) > max_chars:
                remaining_parts = self._force_split_by_length(current_sentence.strip(), max_chars)
                sentences.extend(remaining_parts)
            else:
                sentences.append(current_sentence.strip())
        
        # 合併過短的片段
        return self._merge_short_segments(sentences, max_chars)
    
    def _find_best_split_point(self, text: str, max_chars: int) -> str:
        """在文本中找到最佳的斷句點"""
        if len(text) <= max_chars:
            return text
            
        # 優先順序：強標點 > 中等標點 > 弱標點 > 空格
        primary_punctuation = ['。', '！', '？']
        secondary_punctuation = ['；', '：']
        tertiary_punctuation = ['，', '、']
        
        # 在最大字符數範圍內查找最佳斷點
        best_pos = -1
        best_priority = 0
        
        for i in range(min(len(text), max_chars), max(0, max_chars - 10), -1):
            char = text[i-1] if i > 0 else ''
            priority = 0
            
            if char in primary_punctuation:
                priority = 4
            elif char in secondary_punctuation:
                priority = 3
            elif char in tertiary_punctuation:
                priority = 2
            elif char == ' ' or char.isspace():
                priority = 1
            
            if priority > best_priority:
                best_priority = priority
                best_pos = i
                
            # 如果找到強標點，直接使用
            if priority >= 4:
                break
        
        if best_pos > 0:
            return text[:best_pos]
        else:
            # 如果找不到合適的斷點，在最大字符數處強制斷句
            return text[:max_chars]
    
    def _force_split_by_length(self, text: str, max_chars: int) -> List[str]:
        """按長度強制切分文本"""
        parts = []
        for i in range(0, len(text), max_chars):
            part = text[i:i + max_chars].strip()
            if part:
                parts.append(part)
        return parts
    
    def _merge_short_segments(self, sentences: List[str], max_chars: int) -> List[str]:
        """合併過短的片段，同時保持標點符號斷句的邏輯"""
        if not sentences:
            return []
            
        merged = []
        current = ""
        
        # 定義不應該合併的標點符號（句子結束標點）
        sentence_ending_punctuation = ['。', '！', '？']
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # 檢查當前累積文本的最後一個字符
            should_merge = True
            
            if current:
                # 如果前一個片段以強斷句標點結尾，較謹慎地合併
                last_char = current.strip()[-1] if current.strip() else ''
                if last_char in sentence_ending_punctuation:
                    # 只有在合併後長度較短時才合併
                    if len(current + sentence) > max_chars * 0.7:  # 70% 閾值
                        should_merge = False
                
                # 檢查合併後是否超過限制
                if len(current + sentence) > max_chars:
                    should_merge = False
            
            if should_merge and current:
                current += sentence
            else:
                # 保存當前片段（如果有）
                if current:
                    merged.append(current)
                current = sentence
        
        # 添加最後一個片段
        if current:
            merged.append(current)
        
        # 二次檢查：如果有過短的片段（小於5個字符），嘗試與鄰近片段合併
        final_merged = []
        i = 0
        while i < len(merged):
            current_segment = merged[i]
            
            # 如果片段很短，嘗試與下一個片段合併
            if len(current_segment) < 5 and i + 1 < len(merged):
                next_segment = merged[i + 1]
                if len(current_segment + next_segment) <= max_chars:
                    final_merged.append(current_segment + next_segment)
                    i += 2  # 跳過下一個片段
                    continue
            
            final_merged.append(current_segment)
            i += 1
        
        return final_merged
    
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
            formatted_text = self._format_subtitle_lines(part, self.chars_per_line)
            segments.append({
                "start": current_time,
                "end": part_end_time,
                "text": formatted_text
            })
            
            current_time = part_end_time
        
        return segments
    
    def _format_subtitle_lines(self, text: str, max_chars_per_line: int) -> str:
        """將文字格式化為單行顯示（不換行）"""
        # 直接返回原始文字，不進行換行處理
        return text.strip()
    
    def _format_time(self, seconds: float) -> str:
        """將秒數轉換為 SRT 時間格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds_remainder = seconds % 60
        milliseconds = int((seconds_remainder % 1) * 1000)
        seconds_int = int(seconds_remainder)
        
        return f"{hours:02d}:{minutes:02d}:{seconds_int:02d},{milliseconds:03d}"
    
    def generate_subtitles(self, video_path: str, reference_texts: List[str]) -> str:
        """
        生成字幕 - 使用語速計算方法
        
        Args:
            video_path: 視頻文件路徑
            reference_texts: 用戶提供的參考文字列表（每個元素代表一頁）
            
        Returns:
            SRT 字幕文件路徑
        """
        try:
            logger.info(f"🎬 開始生成字幕（語速計算），視頻: {video_path}")
            logger.info(f"📄 參考文字頁數: {len(reference_texts)}")
            
            # 直接使用語速計算方法生成字幕
            return self.generate_subtitles_by_speech_rate(video_path, reference_texts)
            
        except Exception as e:
            logger.error(f"❌ 字幕生成失敗: {e}")
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
    
    def _split_sentences_by_punctuation(self, text: str) -> List[str]:
        """
        根據標點符號精確切割句子
        
        Args:
            text: 輸入文字
            
        Returns:
            句子列表
        """
        if not text or not text.strip():
            return []
        
        # 中文標點符號列表
        sentence_endings = ['。', '！', '？', '；', '…', '!', '?', ';']
        
        sentences = []
        current_sentence = ""
        
        for char in text:
            current_sentence += char
            
            # 如果遇到句子結束標點
            if char in sentence_endings:
                if current_sentence.strip():
                    sentences.append(current_sentence.strip())
                current_sentence = ""
        
        # 處理最後一個句子（沒有結束標點的情況）
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        # 過濾空句子
        sentences = [s for s in sentences if s.strip()]
        
        return sentences 

    def generate_subtitles_by_speech_rate(self, video_path: str, reference_texts: List[str]) -> str:
        """
        基於語速計算生成字幕 - 無需Whisper，直接用文稿和音頻時長計算
        
        Args:
            video_path: 視頻文件路徑
            reference_texts: 用戶提供的參考文字列表
            
        Returns:
            SRT 字幕文件路徑
        """
        try:
            logger.info(f"📊 開始基於語速生成字幕，視頻: {video_path}")
            logger.info(f"📄 參考文字頁數: {len(reference_texts)}")
            
            # 從視頻提取音頻並獲取時長
            audio_path = self._extract_audio_from_video(video_path)
            audio_duration = self._get_audio_duration(audio_path)
            
            logger.info(f"🎵 音頻時長: {audio_duration:.2f} 秒")
            
            # 合併所有文字
            full_text = "\n".join(reference_texts) if isinstance(reference_texts, list) else reference_texts
            
            # 計算語速
            speech_rate = self._calculate_speech_rate(full_text, audio_duration)
            logger.info(f"📈 計算語速: {speech_rate:.2f} 字/秒")
            
            # 按句子切割文稿
            sentences = []
            for page_index, page_text in enumerate(reference_texts):
                if page_text and page_text.strip():
                    page_sentences = self._split_sentences_by_punctuation(page_text.strip())
                    for sentence in page_sentences:
                        if sentence.strip():
                            sentences.append({
                                'text': sentence.strip(),
                                'page_index': page_index + 1
                            })
            
            logger.info(f"📝 文稿切割: {len(sentences)} 個句子")
            
            # 根據語速分配時間戳
            timestamped_segments = self._assign_timestamps_by_speech_rate(sentences, speech_rate)
            
            # 調整時間戳確保不超過總時長
            adjusted_segments = self._adjust_timestamps_to_duration(timestamped_segments, audio_duration)
            
            # 生成 SRT 內容
            srt_content = self._generate_srt_content(adjusted_segments)
            
            # 保存 SRT 文件（使用統一的命名）
            srt_path = video_path.replace('.mp4', '_subtitles.srt')
            with open(srt_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            logger.info(f"✅ 字幕生成完成: {srt_path}")
            
            # 清理臨時音頻文件
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            return srt_path
            
        except Exception as e:
            logger.error(f"❌ 基於語速的字幕生成失敗: {e}")
            raise e
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """獲取音頻文件時長"""
        try:
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 
                   'format=duration', '-of', 'csv=p=0', audio_path]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"FFprobe 獲取時長失敗: {result.stderr}")
            
            duration = float(result.stdout.strip())
            logger.info(f"🎵 音頻時長: {duration:.2f} 秒")
            return duration
            
        except Exception as e:
            logger.error(f"❌ 獲取音頻時長失敗: {e}")
            # 備用方法：嘗試使用 ffmpeg
            try:
                cmd = ['ffmpeg', '-i', audio_path, '-f', 'null', '-']
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                # 從 stderr 中解析時長
                import re
                duration_match = re.search(r'time=(\d{2}):(\d{2}):(\d{2}\.\d{2})', result.stderr)
                if duration_match:
                    hours, minutes, seconds = duration_match.groups()
                    total_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                    logger.info(f"🎵 音頻時長（備用方法）: {total_seconds:.2f} 秒")
                    return total_seconds
                else:
                    raise Exception("無法解析音頻時長")
                    
            except Exception as backup_e:
                logger.error(f"❌ 備用方法也失敗: {backup_e}")
                raise e
    
    def _count_effective_characters(self, text: str) -> int:
        """計算有效字數（排除標點和空格）"""
        import re
        effective_chars = len(re.sub(r'[^\w]', '', text))
        return effective_chars
    
    def _calculate_pause_time(self, text: str) -> float:
        """計算文本中標點符號的總停頓時間"""
        punctuation_pauses = {
            '。': 0.5, '！': 0.5, '？': 0.5, '；': 0.3,
            '，': 0.2, '、': 0.15, '：': 0.25, '…': 0.4
        }
        
        total_pause_time = 0
        for punct, pause_duration in punctuation_pauses.items():
            count = text.count(punct)
            total_pause_time += count * pause_duration
        
        return total_pause_time
    
    def _calculate_speech_rate(self, text: str, duration: float) -> float:
        """計算實際語速（字/秒）"""
        # 使用幫助方法計算有效字數
        effective_chars = self._count_effective_characters(text)
        
        # 使用幫助方法計算總停頓時間
        total_pause_time = self._calculate_pause_time(text)
        
        # 計算淨語音時間（扣除停頓）
        net_speech_time = duration - total_pause_time
        
        # 確保淨語音時間不會太小
        if net_speech_time <= 0:
            net_speech_time = duration * 0.8  # 保底80%的時間用於說話
        
        speech_rate = effective_chars / net_speech_time
        
        logger.info(f"📊 文字統計: {effective_chars} 個有效字符")
        logger.info(f"⏱️ 預估停頓時間: {total_pause_time:.2f} 秒")
        logger.info(f"🗣️ 淨語音時間: {net_speech_time:.2f} 秒")
        logger.info(f"📈 計算語速: {speech_rate:.2f} 字/秒")
        
        return speech_rate
    
    def _assign_timestamps_by_speech_rate(self, sentences: List[Dict], speech_rate: float) -> List[Dict]:
        """根據語速分配時間戳"""
        segments = []
        current_time = 0.0
        
        # 標點符號停頓時間設定
        punctuation_pauses = {
            '。': 0.5, '！': 0.5, '？': 0.5, '；': 0.3,
            '，': 0.2, '、': 0.15, '：': 0.25, '…': 0.4
        }
        
        for i, sentence_info in enumerate(sentences):
            sentence = sentence_info['text']
            
            # 計算句子的有效字數
            import re
            effective_chars = len(re.sub(r'[^\w]', '', sentence))
            
            # 計算說話時間
            speech_time = effective_chars / speech_rate if effective_chars > 0 else 0.1
            
            # 計算停頓時間
            pause_time = 0.1  # 預設停頓
            for punct, pause_duration in punctuation_pauses.items():
                if sentence.endswith(punct):
                    pause_time = pause_duration
                    break
            
            # 總時間 = 說話時間 + 停頓時間
            total_duration = speech_time + pause_time
            end_time = current_time + total_duration
            
            # 應用繁簡轉換
            final_text = self._convert_chinese(sentence)
            
            segments.append({
                'start': current_time,
                'end': end_time,
                'text': final_text,
                'effective_chars': effective_chars,
                'speech_time': speech_time,
                'pause_time': pause_time,
                'source': 'speech_rate_calculation',
                'page_index': sentence_info['page_index']
            })
            
            logger.info(f"  📝 句子 {i+1}: {current_time:.2f}s-{end_time:.2f}s ({effective_chars}字, {speech_time:.2f}s+{pause_time:.2f}s)")
            logger.info(f"     內容: '{final_text[:30]}...'")
            
            current_time = end_time
        
        return segments
    
    def _adjust_timestamps_to_duration(self, segments: List[Dict], target_duration: float) -> List[Dict]:
        """調整時間戳以匹配目標時長"""
        if not segments:
            return segments
        
        # 計算當前總時長
        current_total = segments[-1]['end']
        
        logger.info(f"⚖️ 時間調整: 計算時長 {current_total:.2f}s → 目標時長 {target_duration:.2f}s")
        
        # 如果時間差異超過1秒，進行縮放調整
        if abs(current_total - target_duration) > 1.0:
            scale_factor = target_duration / current_total
            logger.info(f"🔧 應用縮放比例: {scale_factor:.3f}")
            
            for segment in segments:
                segment['start'] *= scale_factor
                segment['end'] *= scale_factor
            
            logger.info(f"✅ 時間戳調整完成，最終時長: {segments[-1]['end']:.2f}s")
        else:
            logger.info("✅ 時間戳無需調整，誤差在可接受範圍內")
        
        return segments

    def embed_subtitles_in_video(self, input_video_path: str, srt_path: str, output_video_path: str, style: str = "default") -> bool:
        """將字幕嵌入視頻"""
        try:
            logger.info(f"🎬 開始嵌入字幕: {input_video_path}")
            
            # 獲取可用字體
            font_name = get_available_chinese_font()
            logger.info(f"🔤 使用字體: {font_name}")
            
            # 正規化路徑並處理Windows路徑分隔符問題
            normalized_srt_path = srt_path.replace('\\', '/').replace(':', '\\:')
            
            # 檢查檔案狀態
            logger.info(f"📁 輸入視頻: {input_video_path} (存在: {os.path.exists(input_video_path)})")
            logger.info(f"📁 字幕檔案: {srt_path} (存在: {os.path.exists(srt_path)})")
            logger.info(f"📁 輸出路徑: {output_video_path}")
            
            # 檢查SRT檔案內容
            if os.path.exists(srt_path):
                try:
                    with open(srt_path, 'r', encoding='utf-8') as f:
                        srt_content = f.read()
                        srt_lines = srt_content.strip().split('\n')
                        logger.info(f"📝 SRT檔案行數: {len(srt_lines)}")
                        logger.info(f"📝 SRT檔案前5行: {srt_lines[:5]}")
                        if len(srt_content) == 0:
                            logger.error("❌ SRT檔案為空")
                            return False
                except Exception as e:
                    logger.error(f"❌ 無法讀取SRT檔案: {e}")
                    return False
            
            # 嘗試不同的字幕嵌入方法
            def try_subtitle_methods():
                methods = []
                
                # 方法1: 使用動態字體的完整樣式
                if font_name and not font_name.startswith("/"):  # 字體名稱而非路徑
                    style_with_font = f"force_style='FontName={font_name},FontSize=18,PrimaryColour=&Hffffff,SecondaryColour=&Hffffff,OutlineColour=&H0,BackColour=&H80000000,Bold=1,Italic=0,Underline=0,StrikeOut=0,ScaleX=100,ScaleY=100,Spacing=0,Angle=0,BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginL=10,MarginR=10,MarginV=10'"
                    methods.append(("完整樣式", f"subtitles='{normalized_srt_path}':{style_with_font}"))
                
                # 方法2: 簡化樣式
                simple_style = "force_style='FontSize=18,PrimaryColour=&Hffffff,OutlineColour=&H0,Bold=1,Outline=2,Alignment=2'"
                methods.append(("簡化樣式", f"subtitles='{normalized_srt_path}':{simple_style}"))
                
                # 方法3: 最基本的字幕
                methods.append(("基本字幕", f"subtitles='{normalized_srt_path}'"))
                
                return methods
            
            # 嘗試不同的字幕方法
            subtitle_methods = try_subtitle_methods()
            result = None
            
            for method_name, vf_option in subtitle_methods:
                logger.info(f"🎬 嘗試{method_name}方法...")
                
                cmd = [
                    'ffmpeg',
                    '-i', input_video_path,
                    '-vf', vf_option,
                    '-c:a', 'copy',
                    '-y', output_video_path
                ]
                
                logger.info(f"📋 FFmpeg 命令: {' '.join(cmd)}")
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    logger.info(f"🎬 {method_name} 執行完畢 - 返回碼: {result.returncode}")
                    
                    if result.returncode == 0:
                        logger.info(f"✅ {method_name} 成功!")
                        break
                    else:
                        logger.warning(f"⚠️ {method_name} 失敗: {result.stderr}")
                        # 檢查是否是字體相關錯誤
                        if "fontselect" not in result.stderr and "Glyph" not in result.stderr:
                            # 非字體錯誤，停止嘗試其他方法
                            break
                        
                except subprocess.TimeoutExpired:
                    logger.error(f"❌ {method_name} 執行超時")
                    continue
                except Exception as e:
                    logger.error(f"❌ {method_name} 執行異常: {e}")
                    continue
            
            # 如果所有字幕嵌入方法都失敗，最後嘗試外部字幕
            if not result or result.returncode != 0:
                logger.info("🔄 所有字幕嵌入方法失敗，嘗試外部字幕作為最後手段...")
                fallback_cmd = [
                    'ffmpeg',
                    '-i', input_video_path,
                    '-i', srt_path,
                    '-c', 'copy',
                    '-c:s', 'mov_text',
                    '-y', output_video_path
                ]
                
                logger.info(f"📋 外部字幕命令: {' '.join(fallback_cmd)}")
                try:
                    result = subprocess.run(fallback_cmd, capture_output=True, text=True, timeout=300)
                    logger.info(f"🔧 外部字幕執行完畢 - 返回碼: {result.returncode}")
                    if result.stdout:
                        logger.info(f"📝 外部字幕標準輸出: {result.stdout}")
                    if result.stderr:
                        logger.warning(f"⚠️ 外部字幕標準錯誤: {result.stderr}")
                except Exception as e:
                    logger.error(f"❌ 外部字幕執行異常: {e}")
                    return False
            
            # 最終檢查
            if not result or result.returncode != 0:
                logger.error("❌ 所有字幕嵌入方法都失敗了")
                return False
            
            # 檢查輸出檔案是否真的存在
            if not os.path.exists(output_video_path):
                logger.error(f"❌ 輸出視頻檔案不存在: {output_video_path}")
                return False
            
            output_size = os.path.getsize(output_video_path)
            logger.info(f"✅ 字幕嵌入完成: {output_video_path} (大小: {output_size/1024/1024:.2f} MB)")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("❌ FFmpeg 執行超時 (5分鐘)")
            return False
        except Exception as e:
            logger.error(f"❌ 字幕嵌入失敗: {e}")
            return False
