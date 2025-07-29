
# Google Colab 中文字幕設置指南

## 1. 安裝字體 (在 Colab 中執行)
```python
!apt-get update
!apt-get install -y fonts-noto-cjk fonts-noto-cjk-extra fonts-wqy-zenhei fonts-wqy-microhei
!fc-cache -fv
```

## 2. 驗證字體安裝
```python
!fc-list : family | grep -i noto
```

## 3. 使用修正版的字幕生成器
```python
from utility.whisper_subtitle import WhisperSubtitleGenerator

# 創建實例 (會自動檢測 Colab 環境)
subtitle_gen = WhisperSubtitleGenerator()

# 處理視頻 (會自動使用中文字體)
success = subtitle_gen.process_video_with_subtitles(
    input_video_path='your_video.mp4',
    output_video_path='output_with_subtitles.mp4',
    subtitle_style='default',  # 或 'yellow', 'white_box', 'custom'
    language='zh'  # 指定中文
)
```

## 4. 推薦的 Colab 字幕樣式
- default: 適合深色背景
- yellow: 黃色字幕，高對比度
- white_box: 白色字幕配黑色背景框
- custom: 大字體加粗樣式

## 5. 故障排除
如果字幕仍然無法正常顯示：
1. 重新安裝字體套件
2. 重啟 Colab runtime
3. 使用 fallback 方法 (自動觸發)
