# 🎬 字幕功能使用指南

## 功能概述

新的字幕功能使用 OpenAI 的 Whisper AI 技術，可以自動從生成的影片中提取語音並生成準確的字幕，然後使用 FFmpeg 將字幕嵌入到影片中。

## 如何使用

### 1. 編輯文字頁面
在 `edit_text.html` 編輯頁面中，您會看到一個新的 "Video Options" 區塊：

```
📝 Enable Subtitles
Generate and embed subtitles using Whisper AI and FFmpeg
```

### 2. 選擇字幕樣式
當啟用字幕後，您可以選擇以下樣式之一：
- **Default**: 白色文字，黑色外框
- **Yellow**: 黃色文字，黑色外框  
- **White Box**: 白色文字，黑色背景框
- **Custom**: 自定義樣式（粗體白色文字，黑色外框）

### 3. 生成影片
點擊 "🚀 Generate Video" 按鈕後，系統會：
1. 先生成不帶字幕的影片
2. 使用 Whisper AI 從音軌提取語音文字
3. 生成 SRT 字幕檔案
4. 使用 FFmpeg 將字幕嵌入影片
5. 提供最終帶字幕的影片下載

## 技術特點

### Whisper AI 優勢
- 🤖 **高準確度**: OpenAI 最先進的語音識別技術
- 🌍 **多語言支援**: 自動檢測語言（支援中文、英文等）
- 🎯 **詞級時間戳**: 精確的時間同步
- ⚡ **快速處理**: 優化的模型大小平衡速度與準確度

### FFmpeg 整合
- 🎨 **專業字幕**: 支援多種字幕樣式
- 🔧 **高品質嵌入**: 不影響原影片畫質
- 📐 **自適應字體**: 根據影片解析度調整字體大小

## 系統需求

### 必要依賴
- **FFmpeg**: 用於影片處理和字幕嵌入
- **OpenAI Whisper**: 用於語音轉文字
- **Python 3.7+**: 基本運行環境

### 安裝檢查
運行以下命令檢查依賴是否正確安裝：

```bash
python test_subtitle.py
```

如果看到以下輸出表示一切正常：
```
✅ ffmpeg: Available  
✅ whisper: Available
🎉 All tests passed! Subtitle functionality is ready.
```

## 故障排除

### 常見問題

1. **FFmpeg 未找到**
   ```
   ❌ ffmpeg: Missing
   ```
   **解決方案**: 
   - Windows: 下載 FFmpeg 並添加到 PATH
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`

2. **Whisper 模型加載失敗**
   ```
   ❌ Failed to load Whisper model
   ```
   **解決方案**: 
   ```bash
   pip install openai-whisper
   ```

3. **字幕生成但無法嵌入**
   - 檢查 FFmpeg 版本是否支援字幕過濾器
   - 確保影片檔案沒有被其他程序占用

### 性能優化

- **模型大小**: 系統預設使用 "base" 模型，平衡速度與準確度
- **臨時檔案**: 所有中間檔案會自動清理
- **記憶體使用**: Whisper 模型會在需要時載入，處理完成後釋放

## 技術細節

### 處理流程
1. **音軌提取**: `ffmpeg -i video.mp4 -vn -ar 16000 audio.wav`
2. **語音識別**: `whisper.transcribe(audio, word_timestamps=True)`
3. **SRT 生成**: 轉換 Whisper 結果為標準 SRT 格式
4. **字幕嵌入**: `ffmpeg -i video.mp4 -vf subtitles=subs.srt output.mp4`

### 字幕樣式範例
```css
/* Default Style */
FontName=Arial,FontSize=16,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2

/* Yellow Style */  
FontName=Arial,FontSize=16,PrimaryColour=&H00ffff,OutlineColour=&H000000,Outline=2

/* White Box Style */
FontName=Arial,FontSize=16,PrimaryColour=&Hffffff,BackColour=&H000000,BorderStyle=4
```

## 更新日誌

### v1.0.0 (當前版本)
- ✅ 整合 OpenAI Whisper 語音識別
- ✅ 支援多種字幕樣式選擇  
- ✅ 自動語言檢測
- ✅ FFmpeg 字幕嵌入
- ✅ 完整的錯誤處理和回滾機制

---

如有任何問題或建議，請聯繫開發團隊！
