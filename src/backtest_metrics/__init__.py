"""backtest-metrics: pure, dependency-free performance metrics for trading backtests."""

from .core import (
    CRYPTO_DAILY,
    FOREX_DAILY,
    STOCKS_DAILY,
    Drawdown,
    TradeStats,
    cagr,
    calmar,
    drawdown,
    returns_from_equity,
    sharpe,
    sortino,
    summary,
    trade_stats,
)
from .resample import daily_returns, trading_day

__all__ = [
    "CRYPTO_DAILY",
    "FOREX_DAILY",
    "STOCKS_DAILY",
    "Drawdown",
    "TradeStats",
    "cagr",
    "calmar",
    "daily_returns",
    "drawdown",
    "returns_from_equity",
    "sharpe",
    "sortino",
    "summary",
    "trade_stats",
    "trading_day",
]
__version__ = "0.1.0"
