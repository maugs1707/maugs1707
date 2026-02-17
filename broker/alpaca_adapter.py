"""Broker adapter for Alpaca paper trading."""

from __future__ import annotations

import logging
import time
from typing import Any

from alpaca.common.exceptions import APIError
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest

LOGGER = logging.getLogger(__name__)


class AlpacaAdapter:
    """Thin adapter over Alpaca TradingClient with basic retry logic."""

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        paper: bool = True,
        max_retries: int = 3,
        retry_wait_seconds: float = 1.5,
    ) -> None:
        if not api_key or not secret_key:
            raise ValueError("ALPACA_API_KEY and ALPACA_SECRET_KEY are required.")
        self._api_key = api_key
        self._secret_key = secret_key
        self._paper = paper
        self._max_retries = max_retries
        self._retry_wait_seconds = retry_wait_seconds
        self._client: TradingClient = self._build_client()

    def _build_client(self) -> TradingClient:
        return TradingClient(self._api_key, self._secret_key, paper=self._paper)

    def _with_retry(self, operation_name: str, fn: Any) -> Any:
        for attempt in range(1, self._max_retries + 1):
            try:
                return fn()
            except APIError as exc:
                LOGGER.exception(
                    "broker_api_error",
                    extra={"event": "broker_api_error", "operation": operation_name, "attempt": attempt, "error": str(exc)},
                )
                if attempt >= self._max_retries:
                    raise
                self._client = self._build_client()
                time.sleep(self._retry_wait_seconds)

    def get_account(self):
        """Return account snapshot."""
        return self._with_retry("get_account", self._client.get_account)

    def get_positions(self):
        """Return all open positions."""
        return self._with_retry("get_positions", self._client.get_all_positions)

    def submit_order(self, symbol: str, qty: float, side: str, time_in_force: str = "day"):
        """Submit a market order."""
        side_enum = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
        tif_enum = TimeInForce.DAY if time_in_force.lower() == "day" else TimeInForce.GTC
        order_request = MarketOrderRequest(symbol=symbol, qty=qty, side=side_enum, time_in_force=tif_enum)
        return self._with_retry("submit_order", lambda: self._client.submit_order(order_data=order_request))

    def cancel_order(self, order_id: str):
        """Cancel an order by id."""
        return self._with_retry("cancel_order", lambda: self._client.cancel_order_by_id(order_id))

    def get_open_orders(self):
        """List open orders."""
        return self._with_retry("get_open_orders", self._client.get_orders)
