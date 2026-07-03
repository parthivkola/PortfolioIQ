"""CAGR (Compound Annual Growth Rate) calculation."""

from decimal import Decimal


def cagr(beginning_value: Decimal, ending_value: Decimal, days_held: int) -> Decimal | None:
    """Compute CAGR assuming a single lump-sum investment.

    Returns None if inputs are invalid (zero beginning, zero days).
    """
    if beginning_value <= 0 or days_held <= 0:
        return None

    ratio = float(ending_value / beginning_value)
    exponent = 365.0 / days_held
    result = ratio**exponent - 1
    return Decimal(str(round(result, 6)))
