"""Tests for CAGR calculation."""

from decimal import Decimal

from app.analytics.cagr import cagr


class TestCAGR:
    def test_one_year_10_percent(self):
        result = cagr(Decimal("1000"), Decimal("1100"), 365)
        assert result is not None
        assert abs(float(result) - 0.10) < 0.001

    def test_two_year_double(self):
        """1000 -> 2000 over 2 years."""
        result = cagr(Decimal("1000"), Decimal("2000"), 730)
        assert result is not None
        expected = 2**0.5 - 1  # ~41.4%
        assert abs(float(result) - expected) < 0.01

    def test_loss(self):
        result = cagr(Decimal("1000"), Decimal("800"), 365)
        assert result is not None
        assert float(result) < 0

    def test_zero_beginning_returns_none(self):
        assert cagr(Decimal("0"), Decimal("1000"), 365) is None

    def test_zero_days_returns_none(self):
        assert cagr(Decimal("1000"), Decimal("1100"), 0) is None

    def test_short_period(self):
        """High annualized return for short holding period."""
        result = cagr(Decimal("100"), Decimal("110"), 30)
        assert result is not None
        assert float(result) > 0.10  # annualized should be much higher than 10%
