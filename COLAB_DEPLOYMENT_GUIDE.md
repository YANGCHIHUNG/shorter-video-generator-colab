# Google Colab 部署指南

## 🚨 問題解決

### 原始錯誤
```
error: XDG_RUNTIME_DIR not set in the environment.
ALSA lib confmisc.c:855:(parse_card) cannot find card '0'
...
ImportError: cannot import name 'WhisperSubtitleGenerator' from 'utility.whisper_subtitle'
```

### ✅ 解決方案

我們已經修復了所有問題：

1. **音頻系統警告**：添加了環境變數設置來抑制 ALSA 警告
2. **導入錯誤**：重新創建了完整的 `WhisperSubtitleGenerator` 類
3. **Colab 兼容性**：添加了環境檢測和自動字體設置

## 🚀 在 Google Colab 中使用

### 方法 1：使用專用啟動腳本

```python
# 在 Colab cell 中執行
!git clone https://github.com/your-repo/shorter-video-generator-colab.git
%cd shorter-video-generator-colab

# 使用專用啟動腳本
exec(open('start_colab.py').read())
```

### 方法 2：手動設置

```python
# 1. 設置環境變數 (抑制音頻警告)
import os
os.environ['ALSA_PCM_CARD'] = '0'
os.environ['ALSA_PCM_DEVICE'] = '0'
os.environ['XDG_RUNTIME_DIR'] = '/tmp/runtime-root'

# 2. 安裝中文字體
!apt-get update
!apt-get install -y fonts-noto-cjk fonts-noto-cjk-extra fonts-wqy-zenhei fontconfig
!fc-cache -fv

# 3. 安裝 Python 依賴項
!pip install openai-whisper ffmpeg-python

# 4. 啟動應用程式
from app import app
app.run(host='0.0.0.0', port=5000, debug=False)
```

### 方法 3：一鍵修復腳本

```python
# 執行自動修復腳本
exec(open('colab_chinese_subtitle_fix.py').read())

# 然後啟動應用程式
python app.py
```

## 🎯 字幕功能使用

### 基本使用

```python
from utility.whisper_subtitle import WhisperSubtitleGenerator

# 創建實例 (自動檢測 Colab 環境)
subtitle_gen = WhisperSubtitleGenerator()

# 處理視頻並添加中文字幕
success = subtitle_gen.process_video_with_subtitles(
    input_video_path='input.mp4',
    output_video_path='output_with_subtitles.mp4',
    subtitle_style='default',  # 針對 Colab 優化
    language='zh'  # 中文
)

if success:
    print("✅ 字幕生成成功！")
    # 下載結果文件
    from google.colab import files
    files.download('output_with_subtitles.mp4')
```

### 可用字幕樣式

- `default`: 白色字幕，黑色邊框，適合大多數場景
- `yellow`: 黃色字幕，高對比度
- `white_box`: 白色字幕配半透明黑色背景框
- `custom`: 大字體粗體樣式

## 🔧 技術細節

### 環境檢測
系統會自動檢測是否在 Colab 環境中運行：
- 檢查 Colab 環境變數
- 檢查文件路徑特徵
- 檢查 Colab 特定模組

### 字體管理
針對 Colab 環境的特殊設置：
- 自動安裝 Noto CJK 字體
- 更新字體快取
- 設置字體目錄路徑

### 錯誤處理
多層級錯誤處理機制：
1. 主要方法：使用 Noto CJK 字體
2. 倒退方法：使用 WenQuanYi 字體
3. 最終倒退：基本字幕嵌入

## 📋 完整部署檢查清單

- [ ] 克隆儲存庫到 Colab
- [ ] 設置環境變數 (抑制音頻警告)
- [ ] 安裝中文字體支援
- [ ] 安裝 Python 依賴項
- [ ] 驗證 WhisperSubtitleGenerator 導入
- [ ] 測試字幕功能
- [ ] 啟動 Flask 應用程式

## 🎉 成功指標

看到以下訊息表示設置成功：
- `✅ WhisperSubtitleGenerator initialized successfully`
- `✅ Detected Google Colab environment`
- `✅ Chinese fonts installed successfully`
- `✅ Subtitle functionality available`

## 🆘 故障排除

### 如果仍有導入錯誤
```python
# 檢查文件是否存在
import os
print("File exists:", os.path.exists('utility/whisper_subtitle.py'))

# 檢查文件內容
with open('utility/whisper_subtitle.py', 'r') as f:
    print("First 100 chars:", f.read()[:100])
```

### 如果字幕無法顯示
```python
# 重新安裝字體
!apt-get purge fonts-noto-cjk* -y
!apt-get install fonts-noto-cjk fonts-noto-cjk-extra -y
!fc-cache -fv

# 重啟 runtime: Runtime > Restart runtime
```

### 如果 FFmpeg 錯誤
```python
# 檢查 FFmpeg 安裝
!which ffmpeg
!ffmpeg -version

# 測試基本功能
!ffmpeg -f lavfi -i testsrc=duration=10:size=320x240:rate=1 test.mp4
```

## 📞 支援

如果遇到其他問題：
1. 查看完整錯誤日誌
2. 檢查 Colab 環境更新
3. 參考 `COLAB_CHINESE_SUBTITLE_GUIDE.md`
4. 使用 `colab_chinese_subtitle_fix.py` 自動診斷

---

🎬 現在您可以在 Google Colab 中完美使用中文字幕功能了！
