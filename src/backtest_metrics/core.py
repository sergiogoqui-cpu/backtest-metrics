"""Pure performance metrics for backtests and live equity curves. No dependencies."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import asdict, dataclass

# Periods per year for the usual calendars.
CRYPTO_DAILY = 365  # 24/7 markets
STOCKS_DAILY = 252  # exchange trading days
FOREX_DAILY = 260


def returns_from_equity(equity: Sequence[float]) -> list[float]:
    """Simple period returns from an equity curve: ``e[i] / e[i-1] - 1``."""
    out: list[float] = []
    for prev, cur in zip(equity, equity[1:]):
        if prev <= 0:
            raise ValueError("equity must stay positive to compute returns")
        out.append(cur / prev - 1)
    return out


def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def stdev(xs: Sequence[float]) -> float:
    """Sample standard deviation (n-1). 0 when undefined."""
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def sharpe(returns: Sequence[float], periods_per_year: int = CRYPTO_DAILY, risk_free: float = 0.0) -> float:
    """Annualised Sharpe ratio. ``risk_free`` is the annual rate. 0 when undefined."""
    if len(returns) < 2:
        return 0.0
    rf = risk_free / periods_per_year
    sd = stdev(returns)
    if sd == 0:
        return 0.0
    return (mean(returns) - rf) / sd * math.sqrt(periods_per_year)


def sortino(returns: Sequence[float], periods_per_year: int = CRYPTO_DAILY, risk_free: float = 0.0) -> float:
    """Annualised Sortino ratio (downside deviation against the risk-free rate)."""
    if len(returns) < 2:
        return 0.0
    rf = risk_free / periods_per_year
    downside = [min(0.0, r - rf) for r in returns]
    dd = math.sqrt(sum(d * d for d in downside) / len(returns))
    if dd == 0:
        return 0.0
    return (mean(returns) - rf) / dd * math.sqrt(periods_per_year)


@dataclass(frozen=True)
class Drawdown:
    max_drawdown: float  # fraction, e.g. 0.25 = -25%
    peak_index: int
    trough_index: int
    recovery_index: int | None  # None if the curve never regained the peak
    longest_underwater: int  # periods spent below a previous peak


def drawdown(equity: Sequence[float]) -> Drawdown:
    """Maximum drawdown of an equity curve and where it happened."""
    if not equity:
        return Drawdown(0.0, 0, 0, None, 0)
    peak_i = 0
    peak = equity[0]
    worst = 0.0
    w_peak = w_trough = 0
    underwater = longest = 0
    for i, e in enumerate(equity):
        if e >= peak:
            peak, peak_i = e, i
            underwater = 0
        else:
            underwater += 1
            longest = max(longest, underwater)
            dd = (peak - e) / peak
            if dd > worst:
                worst, w_peak, w_trough = dd, peak_i, i
    recovery = None
    if worst > 0:
        target = equity[w_peak]
        recovery = next((i for i in range(w_trough, len(equity)) if equity[i] >= target), None)
    return Drawdown(worst, w_peak, w_trough, recovery, longest)


def cagr(equity: Sequence[float], periods_per_year: int = CRYPTO_DAILY) -> float:
    """Compound annual growth rate from the first to the last point."""
    if len(equity) < 2 or equity[0] <= 0 or equity[-1] <= 0:
        return 0.0
    years = (len(equity) - 1) / periods_per_year
    return (equity[-1] / equity[0]) ** (1 / years) - 1


def calmar(equity: Sequence[float], periods_per_year: int = CRYPTO_DAILY) -> float:
    dd = drawdown(equity).max_drawdown
    return cagr(equity, periods_per_year) / dd if dd > 0 else 0.0


@dataclass(frozen=True)
class TradeStats:
    trades: int
    win_rate: float
    profit_factor: float  # gross profit / gross loss; inf if no losses
    expectancy: float  # average PnL per trade
    avg_win: float
    avg_loss: float  # negative
    payoff_ratio: float  # avg_win / |avg_loss|
    max_consecutive_losses: int
    max_consecutive_wins: int


def trade_stats(pnls: Sequence[float]) -> TradeStats:
    """Statistics from a list of closed-trade profits/losses (any currency unit)."""
    if not pnls:
        return TradeStats(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0)
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    gross_win, gross_loss = sum(wins), -sum(losses)
    avg_win = mean(wins)
    avg_loss = mean(losses)
    best = worst = run_w = run_l = 0
    for p in pnls:
        run_w = run_w + 1 if p > 0 else 0
        run_l = run_l + 1 if p < 0 else 0
        best, worst = max(best, run_w), max(worst, run_l)
    return TradeStats(
        trades=len(pnls),
        win_rate=len(wins) / len(pnls),
        profit_factor=gross_win / gross_loss if gross_loss > 0 else (math.inf if gross_win > 0 else 0.0),
        expectancy=mean(pnls),
        avg_win=avg_win,
        avg_loss=avg_loss,
        payoff_ratio=avg_win / abs(avg_loss) if avg_loss < 0 else 0.0,
        max_consecutive_losses=worst,
        max_consecutive_wins=best,
    )


def summary(
    equity: Sequence[float],
    pnls: Sequence[float] | None = None,
    periods_per_year: int = CRYPTO_DAILY,
    risk_free: float = 0.0,
) -> dict[str, float | int | None]:
    """One flat dict with the headline numbers, ready to print or serialise."""
    rets = returns_from_equity(equity)
    dd = drawdown(equity)
    out: dict[str, float | int | None] = {
        "total_return": equity[-1] / equity[0] - 1 if len(equity) > 1 else 0.0,
        "cagr": cagr(equity, periods_per_year),
        "sharpe": sharpe(rets, periods_per_year, risk_free),
        "sortino": sortino(rets, periods_per_year, risk_free),
        "calmar": calmar(equity, periods_per_year),
        "max_drawdown": dd.max_drawdown,
        "longest_underwater": dd.longest_underwater,
    }
    if pnls is not None:
        out.update(asdict(trade_stats(pnls)))
    return out
