"""Turn timestamped equity points into regular daily returns."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, timedelta


def trading_day(ts: datetime) -> date:
    """UTC day of a bar *close*: a bar closing exactly at midnight belongs to the previous day."""
    return (ts - timedelta(microseconds=1)).date()


def daily_returns(
    curve: Sequence[tuple[datetime, float]], start_equity: float, *, fill_gaps: bool = True
) -> list[float]:
    """Daily returns from ``(timestamp, equity)`` points.

    Uses the last equity of each UTC day. With ``fill_gaps`` a day without data counts as a
    0% return (right for 24/7 markets); otherwise missing days are skipped (stock calendars).
    """
    if not curve:
        return []
    closes: dict[date, float] = {}
    for ts, equity in sorted(curve, key=lambda p: p[0]):
        closes[trading_day(ts)] = equity
    days = sorted(closes)
    returns: list[float] = []
    prev = start_equity
    if fill_gaps:
        day = days[0]
        while day <= days[-1]:
            cur = closes.get(day, prev)
            returns.append(cur / prev - 1)
            prev = cur
            day += timedelta(days=1)
    else:
        for day in days:
            returns.append(closes[day] / prev - 1)
            prev = closes[day]
    return returns
