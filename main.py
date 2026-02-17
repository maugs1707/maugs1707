"""Entrypoint for the trading MVP."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from broker.alpaca_adapter import AlpacaAdapter
from config.settings import settings
from data.market_data import MarketDataProvider
from execution.executor import TradeExecutor
from risk.risk_engine import RiskEngine
from strategy.moving_average import MovingAverageCrossoverStrategy


class JsonFormatter(logging.Formatter):
    """Simple JSON formatter for structured logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "event": getattr(record, "event", None),
        }
        for key in ["symbol", "signal", "confidence", "reason", "qty", "order_id", "error"]:
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        return json.dumps(payload)


def setup_logging(log_path: Path) -> None:
    """Configure file and stdout logging with JSON serialization."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    formatter = JsonFormatter()

    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers = [file_handler, stream_handler]


def run() -> None:
    """Run one deterministic strategy-evaluate-execute cycle."""
    setup_logging(settings.log_path)
    logger = logging.getLogger("trading_engine")

    broker = AlpacaAdapter(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key,
        paper=True,
    )
    market_data_provider = MarketDataProvider()
    strategy = MovingAverageCrossoverStrategy(
        short_window=settings.short_window,
        long_window=settings.long_window,
    )
    risk_engine = RiskEngine(
        max_capital_per_position=settings.max_capital_per_position,
        max_trades_per_day=settings.max_trades_per_day,
        stop_loss_pct=settings.stop_loss_pct,
        max_daily_loss_pct=settings.max_daily_loss_pct,
    )
    executor = TradeExecutor(broker)

    data = market_data_provider.get_ohlcv(settings.default_symbol, period=settings.history_period)
    signal = strategy.generate_signal(settings.default_symbol, data)
    logger.info("signal_generated", extra={"event": "signal_generated", **signal.as_dict()})

    account = broker.get_account()
    equity = float(account.equity)
    daily_pnl = float(getattr(account, "unrealized_pl", 0.0)) + float(getattr(account, "realized_pl", 0.0))

    open_orders = broker.get_open_orders()
    today_trades = risk_engine.count_today_filled_trades(open_orders)

    risk_decision = risk_engine.evaluate(
        signal=signal.signal,
        equity=equity,
        today_trades=today_trades,
        daily_pnl=daily_pnl,
    )
    logger.info(
        "risk_decision",
        extra={"event": "risk_decision", "reason": risk_decision.reason, **risk_decision.as_dict()},
    )

    last_price = float(data["Close"].iloc[-1])
    execution_result = executor.execute(signal, risk_decision, last_price=last_price)
    logger.info(
        "execution_result",
        extra={
            "event": "execution_result",
            "reason": execution_result.reason,
            "qty": execution_result.qty,
            "order_id": execution_result.order_id,
        },
    )


if __name__ == "__main__":
    run()
