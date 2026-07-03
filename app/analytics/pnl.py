"""Realized and unrealized P&L calculations."""

from decimal import Decimal

from app.models.holding import Holding
from app.models.transaction import Transaction


def unrealized_pnl(holding: Holding, current_price: Decimal) -> Decimal:
    """P&L on open position: qty * (market price - avg buy price)."""
    return holding.quantity * (current_price - holding.average_buy_price)


def realized_pnl_from_sells(
    sells: list[Transaction],
    avg_price_at_sale: Decimal,
) -> Decimal:
    """Sum of realized gains from SELL transactions.

    Note: In production this would use the avg buy price at the moment of each sale,
    which the portfolio service computes during transaction processing. This simplified
    version uses a single avg price for illustration; the service layer passes the
    correct per-sale average.
    """
    total = Decimal("0")
    for sell in sells:
        total += sell.quantity * (sell.price - avg_price_at_sale)
    return total


def daily_pnl(holding: Holding, current_price: Decimal, previous_close: Decimal) -> Decimal:
    """Today's P&L for a holding based on price change since yesterday's close."""
    return holding.quantity * (current_price - previous_close)
