"""Decimal serialization helpers for JSON responses."""

from decimal import Decimal


def to_str(value: Decimal | float | None, places: int = 2) -> str:
    """Format a numeric value as a string with fixed decimal places."""
    if value is None:
        return "0.00"
    if isinstance(value, float):
        value = Decimal(str(value))
    return str(value.quantize(Decimal(10) ** -places))


def safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    """Divide two Decimals, returning zero if denominator is zero."""
    if denominator == 0:
        return Decimal("0")
    return numerator / denominator
