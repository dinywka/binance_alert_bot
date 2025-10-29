import os
from unittest.mock import AsyncMock

import dotenv
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

CHECK_INTERVAL = 5
MAX_ALERTS_PER_USER = 10

POPULAR_PAIRS = [
    ("BTCUSDT", "Bitcoin"),
    ("ETHUSDT", "Ethereum"),
    ("BNBUSDT", "Binance Coin"),
    ("SOLUSDT", "Solana"),
    ("LTCUSDT", "Litecoin"),
]

EMOJIS = {
    # Движение цены
    "up": "▲",
    "down": "▼",
    "neutral": "━",

    # Интенсивность
    "fire": "🔥",  # Сильный рост
    "ice": "❄️",  # Сильное падение
    "rocket": "🚀",  # Взлёт
    "crash": "💥",  # Обвал

    # RSI
    "overbought": "⚠️",  # Перекупленность
    "oversold": "💎",  # Перепроданность

    # Объём
    "high_volume": "🔊",
    "low_volume": "🔇",

    # Тренд
    "bull": "🐂",
    "bear": "🐻",

    # Статус
    "success": "✅",
    "warning": "⚠️",
    "error": "❌",
    "info": "ℹ️"
}
