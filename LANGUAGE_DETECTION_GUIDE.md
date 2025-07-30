# 字幕語言處理指南

## 🌍 支援的語言

### 主要語言
| 語言 | 代碼 | Whisper 支援 | 說明 |
|------|------|-------------|------|
| 中文 | zh, zh-cn, zh-tw | ✅ | 簡繁體通用 |
| 英文 | en, en-us, en-gb | ✅ | 美式/英式通用 |
| 日文 | ja | ✅ | 完整支援 |
| 韓文 | ko | ✅ | 完整支援 |
| 西班牙文 | es | ✅ | 完整支援 |
| 法文 | fr | ✅ | 完整支援 |
| 德文 | de | ✅ | 完整支援 |

## 🔧 使用方式

### 1. 自動檢測 (推薦)
```python
# 不指定語言，讓 Whisper 自動檢測
subtitle_gen.process_video_with_subtitles(
    input_video_path='video.mp4',
    output_video_path='output.mp4',
    language=None  # 或不傳入此參數
)
```

### 2. 指定語言
```python
# 指定中文
subtitle_gen.process_video_with_subtitles(
    input_video_path='video.mp4', 
    output_video_path='output.mp4',
    language='zh'
)

# 指定英文
subtitle_gen.process_video_with_subtitles(
    input_video_path='video.mp4',
    output_video_path='output.mp4', 
    language='en'
)
```

## 📊 語言檢測準確性

### 高準確性場景
- ✅ 純單一語言內容
- ✅ 語音清晰，發音標準
- ✅ 背景噪音較少
- ✅ 語音時長超過 10 秒

### 可能需要手動指定
- ⚠️ 多語言混合內容
- ⚠️ 方言或口音較重
- ⚠️ 背景音樂/噪音較大
- ⚠️ 語音片段很短

## 🎯 最佳實踐

1. **預設使用自動檢測**: 對大多數內容效果很好
2. **音質優化**: 清晰的音頻能提高檢測準確性
3. **內容分段**: 長視頻可考慮分段處理
4. **結果驗證**: 檢查生成的字幕內容是否正確

## 🔍 故障排除

### 檢測錯誤的語言
```python
# 手動指定正確的語言
language='zh'  # 強制中文
language='en'  # 強制英文
```

### 混合語言內容
```python
# 使用主要語言
language='zh'  # 如果中文內容較多
```

### 檢測失敗
```python
# 嘗試不同模型大小
subtitle_gen.model_size = 'base'    # 較快
subtitle_gen.model_size = 'small'   # 平衡
subtitle_gen.model_size = 'medium'  # 較準確
```

---

💡 **提示**: 修復後的系統現在能正確處理所有這些語言檢測場景！
