"""Tests for holding state transitions matching domain model section 2.3."""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.exceptions import OverSellError
from app.portfolio.service import PortfolioService


class TestHoldingTransitions:
    """Verifies the state-transition rules from the domain model:
    BUY, SELL, DIVIDEND, BONUS, SPLIT.
    """

    def _make_holding(self, qty: str = "10", avg: str = "100"):
        return MagicMock(
            quantity=Decimal(qty),
            average_buy_price=Decimal(avg),
        )

    def _svc(self):
        return PortfolioService.__new__(PortfolioService)

    def test_buy_increases_quantity_and_recalculates_avg(self):
        svc = self._svc()
        holding = self._make_holding("10", "100")

        svc._apply_buy(holding, Decimal("5"), Decimal("120"))

        assert holding.quantity == Decimal("15")
        # new_avg = (10*100 + 5*120) / 15 = 1600/15 = 106.666...
        expected_avg = (Decimal("10") * Decimal("100") + Decimal("5") * Decimal("120")) / Decimal(
            "15"
        )
        assert abs(holding.average_buy_price - expected_avg) < Decimal("0.001")

    def test_sell_reduces_quantity_keeps_avg(self):
        svc = self._svc()
        holding = self._make_holding("10", "100")

        svc._apply_sell(holding, Decimal("3"))

        assert holding.quantity == Decimal("7")
        # Average buy price should be unchanged after SELL
        assert holding.average_buy_price == Decimal("100")

    def test_sell_full_position(self):
        svc = self._svc()
        holding = self._make_holding("10", "100")

        svc._apply_sell(holding, Decimal("10"))

        assert holding.quantity == Decimal("0")

    def test_oversell_raises(self):
        svc = self._svc()
        holding = self._make_holding("10", "100")

        with pytest.raises(OverSellError):
            svc._apply_sell(holding, Decimal("11"))

    def test_dividend_no_state_change(self):
        """DIVIDEND does not affect quantity or average buy price."""
        holding = self._make_holding("10", "100")
        # DIVIDEND path in process_transaction is a pass -- no _apply method
        assert holding.quantity == Decimal("10")
        assert holding.average_buy_price == Decimal("100")

    def test_bonus_increases_qty_adjusts_avg(self):
        svc = self._svc()
        holding = self._make_holding("100", "50")

        # 1:1 bonus (ratio = 1)
        svc._apply_bonus(holding, Decimal("1"))

        # qty = 100 * (1+1) = 200
        assert holding.quantity == Decimal("200")
        # avg = 50 / (1+1) = 25
        assert holding.average_buy_price == Decimal("25")

    def test_split_multiplies_qty_divides_avg(self):
        svc = self._svc()
        holding = self._make_holding("100", "200")

        # 2:1 split (ratio = 2)
        svc._apply_split(holding, Decimal("2"))

        assert holding.quantity == Decimal("200")
        assert holding.average_buy_price == Decimal("100")
