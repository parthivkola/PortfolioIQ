"""Tax-related analytics: dividend income and loss harvesting candidates."""

from decimal import Decimal

from app.core.config import settings


def find_tax_loss_candidates(
    holdings_with_prices: list[dict],
    threshold: float | None = None,
) -> list[dict]:
    """Identify holdings with unrealized losses exceeding the materiality threshold.

    Args:
        holdings_with_prices: List of dicts with keys:
            holding_id, symbol, quantity, average_buy_price, current_price
        threshold: Minimum absolute loss to surface. Defaults to config value.

    Returns:
        Candidates sorted by largest loss first.
    """
    if threshold is None:
        threshold = settings.tax_loss_materiality_threshold

    candidates = []
    for h in holdings_with_prices:
        qty = Decimal(str(h["quantity"]))
        avg = Decimal(str(h["average_buy_price"]))
        price = Decimal(str(h["current_price"]))
        unrealized = qty * (price - avg)

        if unrealized < 0 and abs(unrealized) >= Decimal(str(threshold)):
            candidates.append(
                {
                    "holding_id": h["holding_id"],
                    "symbol": h["symbol"],
                    "unrealized_loss": str(unrealized.quantize(Decimal("0.01"))),
                }
            )

    return sorted(candidates, key=lambda c: Decimal(c["unrealized_loss"]))


def sum_dividend_income(dividend_transactions: list) -> Decimal:
    """Total dividend income from DIVIDEND transaction records."""
    total = Decimal("0")
    for txn in dividend_transactions:
        total += txn.quantity * txn.price
    return total
