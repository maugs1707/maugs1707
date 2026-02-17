# MVP Trading Engine (Alpaca Paper Trading)

Sistema modular de trading algorítmico en Python, enfocado en un flujo institucional simple:

1. Ingesta de datos OHLCV.
2. Generación de señal determinista (SMA 20/50 crossover).
3. Validación de riesgo.
4. Ejecución de orden.
5. Logging estructurado JSON.

## Estructura

```text
project_root/
├── config/
│   └── settings.py
├── broker/
│   └── alpaca_adapter.py
├── data/
│   └── market_data.py
├── strategy/
│   └── moving_average.py
├── risk/
│   └── risk_engine.py
├── execution/
│   └── executor.py
├── logs/
│   └── trading.log
└── main.py
```

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuración

Exporta variables de entorno (Alpaca paper):

```bash
export ALPACA_API_KEY="tu_api_key"
export ALPACA_SECRET_KEY="tu_secret_key"
export ALPACA_BASE_URL="https://paper-api.alpaca.markets"

# Opcionales
export TRADE_SYMBOL="SPY"
export HISTORY_PERIOD="6mo"
export SMA_SHORT_WINDOW="20"
export SMA_LONG_WINDOW="50"
```

## Ejecución

```bash
python main.py
```

Los logs se escriben en `logs/trading.log` y en consola en formato JSON.

## Diagrama simple del flujo interno

```text
+--------------------+
|   MarketDataLayer  |
|  (OHLCV DataFrame) |
+---------+----------+
          |
          v
+--------------------+
| Strategy Engine    |
| SMA20 vs SMA50     |
| -> BUY/SELL/HOLD   |
+---------+----------+
          |
          v
+--------------------+
| Risk Engine        |
| Position limit     |
| Trades/day         |
| Daily loss control |
+---------+----------+
          |
          v
+--------------------+
| Execution Engine   |
| Qty calc + submit  |
| Alpaca Adapter     |
+---------+----------+
          |
          v
+--------------------+
| Structured Logging |
| signal/risk/order  |
+--------------------+
```

## Notas

- Este MVP ejecuta un solo ciclo (batch). Puede evolucionarse fácilmente a scheduler/event-loop.
- Stop loss del 2% se devuelve como directriz de riesgo en esta iteración; para órdenes bracket, se puede extender en `execution/`.
