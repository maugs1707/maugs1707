"""Market data access layer."""

from __future__ import annotations

import logging

import pandas as pd
import yfinance as yf

LOGGER = logging.getLogger(__name__)


class MarketDataProvider:
    """Fetch and normalize OHLCV history."""

    REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]

    def get_ohlcv(self, symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
        """Return clean OHLCV DataFrame indexed by timestamp."""
        raw_df = yf.download(symbol, period=period, interval=interval, auto_adjust=False, progress=False)
        if raw_df.empty:
            raise ValueError(f"No data received for symbol={symbol}")

        # yfinance can return multi-index columns depending on symbol count.
        if isinstance(raw_df.columns, pd.MultiIndex):
            raw_df.columns = [col[0] for col in raw_df.columns]

        missing_cols = [col for col in self.REQUIRED_COLUMNS if col not in raw_df.columns]
        if missing_cols:
            raise ValueError(f"Missing expected OHLCV columns: {missing_cols}")

        df = raw_df[self.REQUIRED_COLUMNS].copy()
        df = df.dropna(how="any")
        df.index = pd.to_datetime(df.index, utc=True)

        LOGGER.info(
            "market_data_loaded",
            extra={
                "event": "market_data_loaded",
                "symbol": symbol,
                "rows": len(df),
                "start": df.index.min().isoformat(),
                "end": df.index.max().isoformat(),
            },
        )
        return df
