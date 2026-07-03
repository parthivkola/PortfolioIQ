"""Tests for P&L calculation functions."""

from decimal import Decimal
from unittest.mock import MagicMock

from app.analytics.pnl import daily_pnl, realized_pnl_from_sells, unrealized_pnl


class TestUnrealizedPnl:
    def test_profit(self):
        holding = MagicMock(quantity=Decimal("10"), average_buy_price=Decimal("100"))
        result = unrealized_pnl(holding, current_price=Decimal("120"))
        assert result == Decimal("200")

    def test_loss(self):
        holding = MagicMock(quantity=Decimal("10"), average_buy_price=Decimal("100"))
        result = unrealized_pnl(holding, current_price=Decimal("80"))
        assert result == Decimal("-200")

    def test_breakeven(self):
        holding = MagicMock(quantity=Decimal("10"), average_buy_price=Decimal("100"))
        result = unrealized_pnl(holding, current_price=Decimal("100"))
        assert result == Decimal("0")


class TestRealizedPnl:
    def test_single_sell_profit(self):
        sell = MagicMock(quantity=Decimal("5"), price=Decimal("120"))
        result = realized_pnl_from_sells([sell], avg_price_at_sale=Decimal("100"))
        assert result == Decimal("100")

    def test_multiple_sells(self):
        sell1 = MagicMock(quantity=Decimal("5"), price=Decimal("120"))
        sell2 = MagicMock(quantity=Decimal("3"), price=Decimal("90"))
        result = realized_pnl_from_sells([sell1, sell2], avg_price_at_sale=Decimal("100"))
        # 5*(120-100) + 3*(90-100) = 100 + (-30) = 70
        assert result == Decimal("70")


class TestDailyPnl:
    def test_price_up(self):
        holding = MagicMock(quantity=Decimal("10"))
        result = daily_pnl(holding, current_price=Decimal("105"), previous_close=Decimal("100"))
        assert result == Decimal("50")
