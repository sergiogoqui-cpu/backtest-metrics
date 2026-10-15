import math
from datetime import datetime, timezone

import pytest

from backtest_metrics import (
    CRYPTO_DAILY,
    STOCKS_DAILY,
    cagr,
    calmar,
    daily_returns,
    drawdown,
    returns_from_equity,
    sharpe,
    sortino,
    summary,
    trade_stats,
    trading_day,
)


def utc(*a):
    return datetime(*a, tzinfo=timezone.utc)


def test_returns_from_equity():
    assert returns_from_equity([100, 110, 99]) == pytest.approx([0.10, -0.10])
    with pytest.raises(ValueError):
        returns_from_equity([100, 0, 50])


def test_sharpe_matches_manual_calculation():
    rets = [0.01, -0.005, 0.02, 0.0, 0.015]
    m = sum(rets) / 5
    sd = math.sqrt(sum((r - m) ** 2 for r in rets) / 4)
    assert sharpe(rets, 365) == pytest.approx(m / sd * math.sqrt(365))
    assert sharpe(rets, 252) == pytest.approx(m / sd * math.sqrt(252))


def test_sharpe_degenerate_cases_are_zero():
    assert sharpe([]) == 0 and sharpe([0.01]) == 0 and sharpe([0.01, 0.01, 0.01]) == 0


def test_sharpe_risk_free_lowers_ratio():
    rets = [0.01, -0.005, 0.02, 0.0, 0.015]
    assert sharpe(rets, 365, risk_free=0.05) < sharpe(rets, 365)


def test_sortino_ignores_upside_volatility():
    only_up = [0.01, 0.02, 0.03]
    assert sortino(only_up) == 0.0  # no downside: undefined -> 0
    mixed = [0.04, -0.01, 0.04, -0.01]
    assert sortino(mixed) > sharpe(mixed)  # upside swings aren't punished


def test_drawdown_depth_location_and_recovery():
    eq = [100, 120, 90, 100, 130, 117]
    dd = drawdown(eq)
    assert dd.max_drawdown == pytest.approx(0.25)
    assert (dd.peak_index, dd.trough_index, dd.recovery_index) == (1, 2, 4)
    assert dd.longest_underwater == 2  # points 2 and 3 are below the 120 peak


def test_drawdown_never_recovers():
    dd = drawdown([100, 80, 90])
    assert dd.max_drawdown == pytest.approx(0.2) and dd.recovery_index is None


def test_drawdown_monotonic_and_empty():
    assert drawdown([1, 2, 3]).max_drawdown == 0
    assert drawdown([]).max_drawdown == 0


def test_cagr_and_calmar():
    assert cagr([100, 200], periods_per_year=1) == pytest.approx(1.0)
    assert cagr([100], 365) == 0
    curve = [100, 150, 120, 180]
    assert calmar(curve, 3) == pytest.approx(cagr(curve, 3) / 0.2)


def test_trade_stats():
    s = trade_stats([10, -5, 20, -5, -5, 15])
    assert s.trades == 6 and s.win_rate == pytest.approx(0.5)
    assert s.profit_factor == pytest.approx(45 / 15)
    assert s.expectancy == pytest.approx(30 / 6)
    assert s.avg_win == pytest.approx(15) and s.avg_loss == pytest.approx(-5)
    assert s.payoff_ratio == pytest.approx(3)
    assert s.max_consecutive_losses == 2 and s.max_consecutive_wins == 1


def test_trade_stats_edge_cases():
    assert trade_stats([]).trades == 0
    assert trade_stats([5, 5]).profit_factor == math.inf
    assert trade_stats([-1, -2]).profit_factor == 0.0


def test_trading_day_midnight_close_belongs_to_previous_day():
    assert trading_day(utc(2026, 1, 2, 0, 0)).isoformat() == "2026-01-01"
    assert trading_day(utc(2026, 1, 2, 0, 1)).isoformat() == "2026-01-02"


def test_daily_returns_fills_gaps_with_zero():
    curve = [(utc(2026, 1, 1, 12), 110.0), (utc(2026, 1, 3, 12), 121.0)]
    assert daily_returns(curve, 100.0) == pytest.approx([0.10, 0.0, 0.10])


def test_daily_returns_without_gap_filling_and_last_value_per_day():
    curve = [
        (utc(2026, 1, 1, 6), 105.0),
        (utc(2026, 1, 1, 18), 110.0),
        (utc(2026, 1, 3, 12), 121.0),
    ]
    assert daily_returns(curve, 100.0, fill_gaps=False) == pytest.approx([0.10, 0.10])
    assert daily_returns([], 100.0) == []


def test_summary_contains_headline_numbers():
    eq = [100, 101, 99, 103, 104]
    s = summary(eq, pnls=[1, -2, 4, 1], periods_per_year=STOCKS_DAILY)
    for key in ("total_return", "cagr", "sharpe", "sortino", "calmar", "max_drawdown", "win_rate"):
        assert key in s
    assert s["total_return"] == pytest.approx(0.04)
    assert CRYPTO_DAILY == 365
