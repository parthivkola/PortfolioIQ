"""Tests for the XIRR Newton-Raphson solver."""

from datetime import date

import pytest

from app.analytics.xirr import xirr
from app.exceptions import XIRRConvergenceError


class TestXIRR:
    def test_simple_investment_and_return(self):
        """Invest 1000, get back 1100 after one year -- expect ~10% return."""
        flows = [-1000, 1100]
        dates = [date(2025, 1, 1), date(2026, 1, 1)]
        result = xirr(flows, dates)
        assert abs(result - 0.10) < 0.01

    def test_multiple_cash_flows(self):
        """Multiple investments and a final value."""
        flows = [-1000, -500, 1800]
        dates = [date(2025, 1, 1), date(2025, 7, 1), date(2026, 1, 1)]
        result = xirr(flows, dates)
        assert result > 0  # should be positive return

    def test_negative_return(self):
        """Lost money on the investment."""
        flows = [-1000, 800]
        dates = [date(2025, 1, 1), date(2026, 1, 1)]
        result = xirr(flows, dates)
        assert result < 0

    def test_single_cash_flow_raises(self):
        """XIRR with fewer than 2 flows should raise."""
        with pytest.raises(XIRRConvergenceError, match="at least two"):
            xirr([-1000], [date(2025, 1, 1)])

    def test_all_same_sign_raises(self):
        """All negative flows (only investments, no returns) should raise."""
        with pytest.raises(XIRRConvergenceError, match="same sign"):
            xirr([-1000, -500], [date(2025, 1, 1), date(2025, 7, 1)])

    def test_breakeven(self):
        """Invest 1000, get back 1000 after a year -- expect ~0% return."""
        flows = [-1000, 1000]
        dates = [date(2025, 1, 1), date(2026, 1, 1)]
        result = xirr(flows, dates)
        assert abs(result) < 0.01

    def test_high_return(self):
        """Invest 100, get back 200 in 6 months -- high annualized return."""
        flows = [-100, 200]
        dates = [date(2025, 1, 1), date(2025, 7, 1)]
        result = xirr(flows, dates)
        assert result > 1.0  # over 100% annualized
