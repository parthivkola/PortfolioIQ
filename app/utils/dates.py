"""Utility helpers for date math used across analytics modules."""

from datetime import date, datetime


def days_between(d1: date | datetime, d2: date | datetime) -> int:
    """Return the absolute number of days between two dates."""
    if isinstance(d1, datetime):
        d1 = d1.date()
    if isinstance(d2, datetime):
        d2 = d2.date()
    return abs((d2 - d1).days)


def to_date(dt: datetime | date) -> date:
    if isinstance(dt, datetime):
        return dt.date()
    return dt
