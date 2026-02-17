"""Risk checks before order execution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class RiskDecision:
    """Risk validation outcome."""

    approved: bool
    reason: str
    max_position_value: float
    stop_loss_pct: float

    def as_dict(self) -> dict:
        return {
            "approved": self.approved,
            "reason": self.reason,
            "max_position_value": self.max_position_value,
            "stop_loss_pct": self.stop_loss_pct,
        }


class RiskEngine:
    """Implements hard portfolio risk limits."""

    def __init__(
        self,
        max_capital_per_position: float = 0.05,
        max_trades_per_day: int = 2,
        stop_loss_pct: float = 0.02,
        max_daily_loss_pct: float = 0.03,
    ) -> None:
        self.max_capital_per_position = max_capital_per_position
        self.max_trades_per_day = max_trades_per_day
        self.stop_loss_pct = stop_loss_pct
        self.max_daily_loss_pct = max_daily_loss_pct

    def evaluate(
        self,
        *,
        signal: str,
        equity: float,
        today_trades: int,
        daily_pnl: float,
    ) -> RiskDecision:
        """Return approval state and max position value allowed."""
        if signal == "HOLD":
            return RiskDecision(False, "Signal is HOLD", 0.0, self.stop_loss_pct)

        if today_trades >= self.max_trades_per_day:
            return RiskDecision(False, "Daily trade limit reached", 0.0, self.stop_loss_pct)

        daily_loss = abs(min(daily_pnl, 0.0))
        if equity > 0 and (daily_loss / equity) > self.max_daily_loss_pct:
            return RiskDecision(False, "Daily loss limit exceeded", 0.0, self.stop_loss_pct)

        max_position_value = equity * self.max_capital_per_position
        if max_position_value <= 0:
            return RiskDecision(False, "Invalid position sizing from equity", 0.0, self.stop_loss_pct)

        return RiskDecision(True, "Approved", max_position_value, self.stop_loss_pct)

    @staticmethod
    def count_today_filled_trades(orders: list) -> int:
        """Count fills from broker order list for current UTC date."""
        today = datetime.now(timezone.utc).date()
        total = 0
        for order in orders:
            filled_at = getattr(order, "filled_at", None)
            if filled_at and filled_at.date() == today:
                total += 1
        return total
