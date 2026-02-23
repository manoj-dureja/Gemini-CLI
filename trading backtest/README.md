# Indian Equities Backtest Framework

A modular Python framework for backtesting trading strategies specifically designed for Indian equities.

## Features
- Historical data retrieval from Indian exchanges (NSE/BSE).
- Custom strategy implementation using a flexible API.
- Backtesting engine accounting for Indian market costs (STT, brokerage).
- Performance metrics like Sharpe Ratio, Max Drawdown, etc.

## Structure
- `src/data`: Data fetching and management.
- `src/engine`: Core backtest logic.
- `src/strategies`: User-defined trading strategies.
- `src/utils`: Helper functions for financial calculations.
- `tests`: Unit and integration tests.
