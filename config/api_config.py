# API 重試配置

# Gemini API 重試設置
GEMINI_MAX_RETRIES = 10  # 最大重試次數
GEMINI_BASE_DELAY = 5    # 基礎延遲時間（秒）
GEMINI_MAX_DELAY = 300   # 最大延遲時間（秒）

# 不同錯誤類型的處理策略
ERROR_HANDLING_CONFIG = {
    "503_UNAVAILABLE": {
        "max_retries": 15,
        "base_delay": 5,
        "max_delay": 120,
        "backoff_multiplier": 2,
        "description": "服務不可用（過載）"
    },
    "429_QUOTA_EXCEEDED": {
        "max_retries": 5,
        "base_delay": 10,
        "max_delay": 300,
        "backoff_multiplier": 3,
        "description": "API 配額超限"
    },
    "500_INTERNAL_ERROR": {
        "max_retries": 8,
        "base_delay": 3,
        "max_delay": 60,
        "backoff_multiplier": 2,
        "description": "內部服務器錯誤"
    },
    "RESOURCE_EXHAUSTED": {
        "max_retries": 10,
        "base_delay": 2,
        "max_delay": 60,
        "backoff_multiplier": 2,
        "description": "資源耗盡"
    }
}

# 用戶友好的錯誤消息
USER_FRIENDLY_MESSAGES = {
    "503": "🚫 AI 服務目前過載，請稍後再試。這是暫時性問題，通常幾分鐘後就會恢復正常。",
    "429": "⏰ API 配額已用完，請稍後再試或檢查 API 金鑰配置。",
    "500": "🔧 AI 服務內部錯誤，請稍後再試。",
    "401": "🔑 API 金鑰無效或已過期，請檢查配置。",
    "UNAVAILABLE": "🚫 AI 服務暫時不可用，請稍後再試。",
    "OVERLOADED": "🚫 AI 服務目前過載，請稍後再試。",
    "RESOURCE_EXHAUSTED": "⏰ API 資源已用完，請稍後再試。"
}

# 重試建議
RETRY_SUGGESTIONS = {
    "503": "建議等待 2-5 分鐘後再次嘗試",
    "429": "建議等待 10-30 分鐘後再次嘗試",
    "500": "建議等待 1-3 分鐘後再次嘗試",
    "UNAVAILABLE": "建議等待 2-5 分鐘後再次嘗試",
    "OVERLOADED": "建議等待 2-5 分鐘後再次嘗試"
}
