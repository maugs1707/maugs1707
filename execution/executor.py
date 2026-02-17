"""Order execution module."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from broker.alpaca_adapter import AlpacaAdapter
from risk.risk_engine import RiskDecision
from strategy.moving_average import StrategySignal

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExecutionResult:
    """Execution status object."""

    executed: bool
    reason: str
    qty: float
    order_id: str | None = None

    def as_dict(self) -> dict:
        return {
            "executed": self.executed,
            "reason": self.reason,
            "qty": self.qty,
            "order_id": self.order_id,
        }


class TradeExecutor:
    """Executes validated trade signals via broker."""

    def __init__(self, broker: AlpacaAdapter) -> None:
        self.broker = broker

    def execute(
        self,
        signal: StrategySignal,
        risk_decision: RiskDecision,
        last_price: float,
    ) -> ExecutionResult:
        """Place order only when risk approves and signal is tradable."""
        if not risk_decision.approved:
            return ExecutionResult(False, risk_decision.reason, 0.0)

        if signal.signal not in {"BUY", "SELL"}:
            return ExecutionResult(False, f"Unsupported signal {signal.signal}", 0.0)

        if last_price <= 0:
            return ExecutionResult(False, "Invalid market price", 0.0)

        qty = round(risk_decision.max_position_value / last_price, 4)
        if qty <= 0:
            return ExecutionResult(False, "Calculated quantity is zero", 0.0)

        try:
            order = self.broker.submit_order(symbol=signal.symbol, qty=qty, side=signal.signal)
            LOGGER.info(
                "order_submitted",
                extra={
                    "event": "order_submitted",
                    "symbol": signal.symbol,
                    "side": signal.signal,
                    "qty": qty,
                    "order_id": str(getattr(order, "id", "")),
                },
            )
            return ExecutionResult(True, "Order submitted", qty, str(getattr(order, "id", None)))
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception(
                "order_submission_failed",
                extra={"event": "order_submission_failed", "error": str(exc), "symbol": signal.symbol},
            )
            return ExecutionResult(False, str(exc), qty)
