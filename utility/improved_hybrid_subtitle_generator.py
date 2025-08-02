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

class ImprovedHybridSubtitleGenerator:
    """改進的混合字幕生成器 - 智能時間戳映射和字幕長度控制"""
    
    def __init__(self, model_size: str = "small", traditional_chinese: bool = False, subtitle_length_mode: str = "auto", chars_per_line: int = 15, max_lines: int = 2):
        """
        初始化混合字幕生成器 - 簡化版本，完全使用用戶輸入文字
        
        Args:
            model_size: Whisper 模型大小 ("tiny", "small", "medium", "large")
            traditional_chinese: 是否使用繁體中文
            subtitle_length_mode: 字幕長度控制模式 ('auto', 'compact', 'standard', 'relaxed')
            chars_per_line: 每行最大字數
            max_lines: 最大行數
        """
        self.model_size = model_size
        self.traditional_chinese = traditional_chinese
        self.subtitle_length_mode = subtitle_length_mode
        self._whisper_model = None
        
        # 設置字幕顯示參數
        self.chars_per_line = chars_per_line
        self.max_lines = max_lines
        self.min_display_time = 1.5  # 最小顯示時間（秒）
        
        # 根據模式調整參數
        if subtitle_length_mode == 'compact':
            self.chars_per_line = min(chars_per_line, 12)
            self.min_display_time = 1.8
        elif subtitle_length_mode == 'relaxed':
            self.chars_per_line = max(chars_per_line, 18)
            self.min_display_time = 1.2
        
        logger.info(f"📏 字幕長度配置: {subtitle_length_mode} - 每行{self.chars_per_line}字，最多{self.max_lines}行")
        
        # 導入所需模組
        try:
            import whisper
            self.whisper = whisper
            logger.info(f"✅ Whisper 模組載入成功，模型大小: {model_size}")
        except ImportError:
            logger.error("❌ 無法導入 Whisper 模組")
            raise ImportError("需要安裝 openai-whisper: pip install openai-whisper")
        
        # 中文轉換模組（可選）
        try:
            import zhconv
            self.zhconv = zhconv
            logger.info("✅ 中文轉換模組載入成功")
        except ImportError:
            logger.warning("⚠️ 中文轉換模組未安裝，將跳過繁簡轉換")
            self.zhconv = None
    
    
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
        生成混合字幕 - 完全使用用戶輸入文字，僅從Whisper獲取時間軸
        
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
            
            # 使用 Whisper 轉錄音頻獲取時間戳（僅用於時間軸）
            whisper_segments = self.transcribe_audio(audio_path)
            
            # 直接映射用戶文字到時間軸（不進行錯字檢測或修正）
            mapped_segments = self._simple_map_user_text_to_timeline(whisper_segments, reference_texts)
            
            # 生成 SRT 內容
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
    
    def _simple_map_user_text_to_timeline(self, whisper_segments: List[Dict], reference_texts) -> List[Dict]:
        """
        簡單映射用戶文字到時間軸 - 完全使用用戶輸入文字
        不進行任何錯字檢測或修正，只進行時間分配
        """
        mapped_segments = []
        
        if not whisper_segments or not reference_texts:
            logger.warning("⚠️ Whisper片段或用戶文字為空")
            return mapped_segments
        
        # 處理單一字串的情況
        if isinstance(reference_texts, str):
            reference_texts = [reference_texts]
        
        logger.info(f"🧠 開始映射：{len(reference_texts)} 個用戶文字 → {len(whisper_segments)} 個 Whisper 片段")
        
        # 準備用戶文字（不進行任何修正）
        all_user_texts = []
        for page_index, page_text in enumerate(reference_texts):
            if page_text and page_text.strip():
                # 將每頁文字分割成句子
                sentences = self._smart_split_text_into_sentences(page_text.strip())
                for sentence in sentences:
                    if sentence.strip():
                        all_user_texts.append({
                            'text': sentence.strip(),
                            'page_index': page_index + 1
                        })
        
        logger.info(f"📝 總共分割出 {len(all_user_texts)} 個句子")
        
        if not all_user_texts:
            logger.error("❌ 沒有有效的用戶文字")
            return mapped_segments
        
        # 計算總時長
        total_duration = whisper_segments[-1]['end'] - whisper_segments[0]['start']
        logger.info(f"📏 總時長: {total_duration:.2f} 秒")
        
        # 簡單時間分配：根據文字數量平均分配時間
        time_per_segment = total_duration / len(all_user_texts)
        current_time = whisper_segments[0]['start']
        
        for i, user_text_info in enumerate(all_user_texts):
            text = user_text_info['text']
            
            # 計算這個片段的時間
            start_time = current_time
            
            # 根據文字長度動態調整時間長度
            char_count = len(text)
            min_duration = max(self.min_display_time, char_count * 0.08)  # 每字至少0.08秒
            
            if i == len(all_user_texts) - 1:
                # 最後一個片段使用剩餘時間
                end_time = whisper_segments[-1]['end']
            else:
                # 使用計算的時間，但不少於最小顯示時間
                duration = max(time_per_segment, min_duration)
                end_time = start_time + duration
            
            # 應用繁簡轉換（如果需要）
            final_text = self._convert_chinese(text)
            
            mapped_segments.append({
                "start": start_time,
                "end": end_time,
                "text": final_text,
                "source": "user_input",  # 標記為用戶輸入
                "page_index": user_text_info['page_index']
            })
            
            current_time = end_time
            
            logger.info(f"  📝 片段 {i+1}: {start_time:.2f}s-{end_time:.2f}s, 頁{user_text_info['page_index']}, '{text[:20]}...'")
        
        logger.info(f"✅ 映射完成，生成 {len(mapped_segments)} 個字幕片段")
        return mapped_segments
    
    def embed_subtitles_in_video(self, input_video_path: str, srt_path: str, output_video_path: str, style: str = "default") -> bool:
        """將字幕嵌入視頻"""
        try:
            logger.info(f"🎬 開始嵌入字幕: {input_video_path}")
            
            # 檢測系統並選擇合適的字體
            def get_available_chinese_font():
                """獲取可用的中文字體"""
                import platform
                system = platform.system().lower()
                
                # 常見的中文字體路徑
                font_paths = []
                
                if system == "linux":
                    # Linux 系統常見的中文字體路徑
                    font_paths = [
                        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                        "/usr/share/fonts/truetype/arphic/ukai.ttc",
                        "/usr/share/fonts/truetype/arphic/uming.ttc",
                        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                        "/System/Library/Fonts/Arial.ttf",  # 有些Linux系統有這個
                    ]
                    # 字體名稱替代（如果找不到檔案）
                    font_names = [
                        "Noto Sans CJK SC",
                        "Noto Sans CJK TC", 
                        "AR PL UKai CN",
                        "AR PL UMing CN",
                        "DejaVu Sans",
                        "Liberation Sans",
                        "Arial"
                    ]
                elif system == "darwin":  # macOS
                    font_paths = [
                        "/System/Library/Fonts/PingFang.ttc",
                        "/Library/Fonts/Arial Unicode MS.ttf",
                        "/System/Library/Fonts/Arial.ttf"
                    ]
                else:  # Windows
                    font_paths = [
                        "C:/Windows/Fonts/msyh.ttc",  # Microsoft YaHei
                        "C:/Windows/Fonts/simhei.ttf",  # SimHei
                        "C:/Windows/Fonts/simsun.ttc",  # SimSun
                        "C:/Windows/Fonts/arial.ttf"
                    ]
                    font_names = [
                        "Microsoft YaHei",
                        "SimHei",
                        "SimSun",
                        "Arial"
                    ]
                
                # 首先檢查字體檔案是否存在
                for i, font_path in enumerate(font_paths):
                    if os.path.exists(font_path):
                        logger.info(f"✅ 找到可用字體檔案: {font_path}")
                        return font_path
                
                # 如果沒有找到字體檔案，嘗試使用字體名稱
                logger.warning("⚠️ 未找到字體檔案，嘗試使用字體名稱")
                if system == "linux":
                    return font_names[0] if font_names else "DejaVu Sans"
                elif system == "darwin":
                    return "Arial"
                else:
                    return font_names[0] if font_names else "Arial"
            
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
                    style_with_font = f"force_style='FontName={font_name},FontSize=24,PrimaryColour=&Hffffff,SecondaryColour=&Hffffff,OutlineColour=&H0,BackColour=&H80000000,Bold=1,Italic=0,Underline=0,StrikeOut=0,ScaleX=100,ScaleY=100,Spacing=0,Angle=0,BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginL=10,MarginR=10,MarginV=10'"
                    methods.append(("完整樣式", f"subtitles='{normalized_srt_path}':{style_with_font}"))
                
                # 方法2: 簡化樣式
                simple_style = "force_style='FontSize=24,PrimaryColour=&Hffffff,OutlineColour=&H0,Bold=1,Outline=2,Alignment=2'"
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
                    logger.info(f"� {method_name} 執行完畢 - 返回碼: {result.returncode}")
                    
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
