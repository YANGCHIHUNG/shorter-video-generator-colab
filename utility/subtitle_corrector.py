"""
字幕校正工具 - 使用既有文字修正Whisper產生的字幕錯字
Subtitle Corrector - Use existing text to correct Whisper-generated subtitle errors
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from fuzzywuzzy import fuzz, process
import difflib

logger = logging.getLogger(__name__)

class SubtitleCorrector:
    """字幕校正器 - 使用參考文字修正Whisper轉錄錯誤"""
    
    def __init__(self, similarity_threshold: int = 70, strict_mode: bool = False):
        """
        初始化字幕校正器
        
        Args:
            similarity_threshold: 相似度閾值 (0-100)，高於此值才進行校正
            strict_mode: 嚴格模式，只在高相似度時才校正
        """
        self.similarity_threshold = similarity_threshold
        self.strict_mode = strict_mode
        logger.info(f"🔧 SubtitleCorrector initialized with threshold={similarity_threshold}%, strict_mode={strict_mode}")
    
    def correct_subtitle_segments(self, whisper_segments: List[Dict], reference_texts: List[str]) -> List[Dict]:
        """
        校正字幕片段
        
        Args:
            whisper_segments: Whisper產生的字幕片段
            reference_texts: 參考文字列表（每個元素對應一頁/一段落）
        
        Returns:
            校正後的字幕片段
        """
        logger.info(f"🔍 Starting subtitle correction for {len(whisper_segments)} segments with {len(reference_texts)} reference texts")
        
        # 將參考文字拆分為句子
        all_reference_sentences = []
        for ref_text in reference_texts:
            sentences = self._split_into_sentences(ref_text)
            all_reference_sentences.extend(sentences)
        
        logger.info(f"📝 Total reference sentences: {len(all_reference_sentences)}")
        
        corrected_segments = []
        correction_stats = {"corrected": 0, "unchanged": 0, "partial": 0}
        
        for i, segment in enumerate(whisper_segments):
            original_text = segment['text'].strip()
            
            if not original_text:
                corrected_segments.append(segment)
                continue
            
            # 尋找最佳匹配的參考文字
            corrected_text, correction_type = self._find_best_correction(
                original_text, all_reference_sentences
            )
            
            # 更新統計
            correction_stats[correction_type] += 1
            
            # 創建校正後的片段
            corrected_segment = segment.copy()
            corrected_segment['text'] = corrected_text
            corrected_segment['original_text'] = original_text  # 保留原始文字
            corrected_segment['correction_type'] = correction_type
            
            if correction_type != "unchanged":
                logger.debug(f"✏️ Segment {i+1}: '{original_text[:30]}...' → '{corrected_text[:30]}...' ({correction_type})")
            
            corrected_segments.append(corrected_segment)
        
        logger.info(f"📊 Correction completed: {correction_stats['corrected']} corrected, "
                   f"{correction_stats['partial']} partial, {correction_stats['unchanged']} unchanged")
        
        return corrected_segments
    
    def _find_best_correction(self, whisper_text: str, reference_sentences: List[str]) -> Tuple[str, str]:
        """
        為單個Whisper文字找到最佳校正
        
        Args:
            whisper_text: Whisper轉錄的文字
            reference_sentences: 參考句子列表
        
        Returns:
            (校正後的文字, 校正類型)
        """
        if not reference_sentences:
            return whisper_text, "unchanged"
        
        # 清理文字用於比較
        cleaned_whisper = self._clean_text_for_comparison(whisper_text)
        
        # 找到最相似的參考句子
        best_match = process.extractOne(
            cleaned_whisper, 
            [self._clean_text_for_comparison(ref) for ref in reference_sentences],
            scorer=fuzz.ratio
        )
        
        if not best_match:
            return whisper_text, "unchanged"
        
        best_score = best_match[1]
        best_index = next(i for i, ref in enumerate(reference_sentences) 
                         if self._clean_text_for_comparison(ref) == best_match[0])
        best_reference = reference_sentences[best_index]
        
        # 根據相似度決定校正策略
        if best_score >= self.similarity_threshold:
            # 高相似度：直接使用參考文字
            logger.debug(f"🎯 High similarity ({best_score}%): using reference text")
            return best_reference, "corrected"
        elif best_score >= 60 and not self.strict_mode:
            # 中等相似度：嘗試部分校正
            partial_corrected = self._partial_correction(whisper_text, best_reference)
            if partial_corrected != whisper_text:
                logger.debug(f"🔧 Partial correction ({best_score}%): some words corrected")
                return partial_corrected, "partial"
        
        return whisper_text, "unchanged"
    
    def _partial_correction(self, whisper_text: str, reference_text: str) -> str:
        """
        部分校正：修正明顯的錯字但保持時間軸對應
        """
        try:
            # 按詞分割
            whisper_words = self._segment_chinese_text(whisper_text)
            reference_words = self._segment_chinese_text(reference_text)
            
            # 使用序列比對找到對應關係
            matcher = difflib.SequenceMatcher(None, whisper_words, reference_words)
            
            corrected_words = []
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'equal':
                    # 相同的部分保持不變
                    corrected_words.extend(whisper_words[i1:i2])
                elif tag == 'replace':
                    # 替換的部分：如果長度相似，使用參考文字
                    whisper_part = whisper_words[i1:i2]
                    reference_part = reference_words[j1:j2]
                    
                    if len(whisper_part) == len(reference_part):
                        corrected_words.extend(reference_part)
                    else:
                        corrected_words.extend(whisper_part)
                elif tag == 'delete':
                    # 删除的部分保留
                    corrected_words.extend(whisper_words[i1:i2])
                elif tag == 'insert':
                    # 插入的部分跳過
                    pass
            
            return ''.join(corrected_words)
        
        except Exception as e:
            logger.warning(f"⚠️ Partial correction failed: {e}")
            return whisper_text
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """將文字分割為句子"""
        # 中文句子分隔符
        sentences = re.split(r'[。！？\.\!\?；;]', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _clean_text_for_comparison(self, text: str) -> str:
        """清理文字用於比較（移除標點符號和空格）"""
        # 移除所有標點符號和空格
        cleaned = re.sub(r'[^\w]', '', text)
        return cleaned.lower()
    
    def _segment_chinese_text(self, text: str) -> List[str]:
        """
        簡單的中文文字分詞（按字符分割）
        在沒有專業分詞工具的情況下的基本實現
        """
        # 對於中文，按字符分割
        # 對於英文和數字，保持完整詞彙
        segments = []
        current_word = ""
        
        for char in text:
            if char.isascii() and char.isalnum():
                # 英文字母和數字
                current_word += char
            else:
                # 中文字符或標點符號
                if current_word:
                    segments.append(current_word)
                    current_word = ""
                if char.strip():  # 忽略空白字符
                    segments.append(char)
        
        if current_word:
            segments.append(current_word)
        
        return segments

class EnhancedWhisperSubtitleGenerator:
    """
    增強版Whisper字幕生成器，整合字幕校正功能
    """
    
    def __init__(self, original_generator, reference_texts: List[str], 
                 enable_correction: bool = True, correction_threshold: int = 70):
        """
        初始化增強版字幕生成器
        
        Args:
            original_generator: 原始的WhisperSubtitleGenerator實例
            reference_texts: 參考文字列表
            enable_correction: 是否啟用字幕校正
            correction_threshold: 校正閾值
        """
        self.original_generator = original_generator
        self.reference_texts = reference_texts
        self.enable_correction = enable_correction
        
        if enable_correction:
            self.corrector = SubtitleCorrector(
                similarity_threshold=correction_threshold
            )
            logger.info(f"✅ Enhanced subtitle generator with correction enabled (threshold: {correction_threshold}%)")
        else:
            self.corrector = None
            logger.info("📝 Enhanced subtitle generator with correction disabled")
    
    def generate_corrected_srt(self, audio_path: str, srt_path: Optional[str] = None, 
                              language: Optional[str] = None) -> str:
        """
        生成校正後的SRT字幕檔案
        
        Args:
            audio_path: 音檔路徑
            srt_path: 輸出SRT檔案路徑
            language: 語言代碼
        
        Returns:
            SRT檔案路徑
        """
        try:
            logger.info(f"🎬 Generating corrected subtitles for: {audio_path}")
            
            # 使用原始生成器進行Whisper轉錄
            original_srt_path = self.original_generator.generate_srt_from_audio(
                audio_path, srt_path, language
            )
            
            if not self.enable_correction or not self.corrector:
                logger.info("📝 Correction disabled, returning original SRT")
                return original_srt_path
            
            # 讀取原始SRT內容
            segments = self._parse_srt_file(original_srt_path)
            
            # 執行校正
            corrected_segments = self.corrector.correct_subtitle_segments(
                segments, self.reference_texts
            )
            
            # 生成校正後的SRT檔案
            corrected_srt_path = original_srt_path.replace('.srt', '_corrected.srt')
            self._write_corrected_srt(corrected_segments, corrected_srt_path)
            
            logger.info(f"✅ Corrected SRT saved to: {corrected_srt_path}")
            return corrected_srt_path
            
        except Exception as e:
            logger.error(f"❌ Error generating corrected subtitles: {e}")
            # 返回原始SRT作為備選
            return self.original_generator.generate_srt_from_audio(audio_path, srt_path, language)
    
    def _parse_srt_file(self, srt_path: str) -> List[Dict]:
        """解析SRT檔案為片段列表"""
        segments = []
        
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            blocks = content.split('\n\n')
            
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 3:
                    # 解析時間軸
                    time_line = lines[1]
                    start_str, end_str = time_line.split(' --> ')
                    
                    start_seconds = self._timestamp_to_seconds(start_str)
                    end_seconds = self._timestamp_to_seconds(end_str)
                    
                    # 文字內容
                    text = '\n'.join(lines[2:])
                    
                    segments.append({
                        'start': start_seconds,
                        'end': end_seconds,
                        'text': text
                    })
        
        except Exception as e:
            logger.error(f"❌ Error parsing SRT file: {e}")
        
        return segments
    
    def _timestamp_to_seconds(self, timestamp: str) -> float:
        """將SRT時間格式轉換為秒數"""
        # 格式: HH:MM:SS,mmm
        time_part, ms_part = timestamp.split(',')
        h, m, s = map(int, time_part.split(':'))
        ms = int(ms_part)
        
        return h * 3600 + m * 60 + s + ms / 1000.0
    
    def _write_corrected_srt(self, segments: List[Dict], output_path: str):
        """寫入校正後的SRT檔案"""
        srt_content = ""
        
        for i, segment in enumerate(segments, 1):
            start_time = self._seconds_to_timestamp(segment['start'])
            end_time = self._seconds_to_timestamp(segment['end'])
            text = segment['text']
            
            srt_content += f"{i}\n"
            srt_content += f"{start_time} --> {end_time}\n"
            srt_content += f"{text}\n\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
    
    def _seconds_to_timestamp(self, seconds: float) -> str:
        """將秒數轉換為SRT時間格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
