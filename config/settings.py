"""Centralized settings for the trading engine."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Runtime configuration loaded from environment variables."""

    alpaca_api_key: str = os.getenv("ALPACA_API_KEY", "")
    alpaca_secret_key: str = os.getenv("ALPACA_SECRET_KEY", "")
    alpaca_base_url: str = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    default_symbol: str = os.getenv("TRADE_SYMBOL", "SPY")
    timeframe: str = os.getenv("TRADE_TIMEFRAME", "1Day")
    history_period: str = os.getenv("HISTORY_PERIOD", "6mo")
    short_window: int = int(os.getenv("SMA_SHORT_WINDOW", "20"))
    long_window: int = int(os.getenv("SMA_LONG_WINDOW", "50"))

    max_capital_per_position: float = float(os.getenv("MAX_CAPITAL_PER_POSITION", "0.05"))
    max_trades_per_day: int = int(os.getenv("MAX_TRADES_PER_DAY", "2"))
    stop_loss_pct: float = float(os.getenv("STOP_LOSS_PCT", "0.02"))
    max_daily_loss_pct: float = float(os.getenv("MAX_DAILY_LOSS_PCT", "0.03"))

    log_path: Path = Path(os.getenv("TRADING_LOG_PATH", "logs/trading.log"))


settings = Settings()
