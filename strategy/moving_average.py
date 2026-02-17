"""Deterministic moving average crossover strategy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd


@dataclass(frozen=True)
class StrategySignal:
    """Structured output for downstream engines."""

    symbol: str
    signal: str
    confidence: float
    timestamp: str

    def as_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "signal": self.signal,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }


class MovingAverageCrossoverStrategy:
    """Simple MA cross strategy using short and long SMAs."""

    def __init__(self, short_window: int = 20, long_window: int = 50) -> None:
        if short_window >= long_window:
            raise ValueError("short_window must be < long_window")
        self.short_window = short_window
        self.long_window = long_window

    def generate_signal(self, symbol: str, data: pd.DataFrame) -> StrategySignal:
        """Generate BUY/SELL/HOLD based on crossover."""
        if len(data) < self.long_window:
            raise ValueError("Insufficient data for long SMA window")

        df = data.copy()
        df["sma_short"] = df["Close"].rolling(window=self.short_window).mean()
        df["sma_long"] = df["Close"].rolling(window=self.long_window).mean()

        prev_short, prev_long = df[["sma_short", "sma_long"]].iloc[-2]
        curr_short, curr_long = df[["sma_short", "sma_long"]].iloc[-1]

        if prev_short <= prev_long and curr_short > curr_long:
            signal = "BUY"
        elif prev_short >= prev_long and curr_short < curr_long:
            signal = "SELL"
        else:
            signal = "HOLD"

        spread = abs(curr_short - curr_long) / curr_long if curr_long else 0.0
        confidence = min(0.99, round(0.5 + spread * 10, 2)) if signal != "HOLD" else 0.5

        return StrategySignal(
            symbol=symbol,
            signal=signal,
            confidence=float(confidence),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
