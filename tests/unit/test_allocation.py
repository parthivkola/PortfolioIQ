"""Tests for allocation and diversification scoring."""

from decimal import Decimal

from app.analytics.allocation import compute_allocation, diversification_score


class TestDiversificationScore:
    def test_single_holding(self):
        """Fully concentrated = score 0."""
        result = diversification_score([Decimal("1.0")])
        assert result == Decimal("0")

    def test_two_equal_holdings(self):
        """Two equal holdings: HHI = 0.5, score = 0.5."""
        result = diversification_score([Decimal("0.5"), Decimal("0.5")])
        assert result == Decimal("0.5")

    def test_well_diversified(self):
        """Five equal holdings: HHI = 0.2, score = 0.8."""
        weights = [Decimal("0.2")] * 5
        result = diversification_score(weights)
        assert abs(result - Decimal("0.8")) < Decimal("0.001")

    def test_empty(self):
        assert diversification_score([]) == Decimal("0")


class TestComputeAllocation:
    def test_basic_allocation(self):
        values = {"STOCK": Decimal("7000"), "MUTUAL_FUND": Decimal("3000")}
        result = compute_allocation(values, Decimal("10000"))
        assert len(result) == 2
        # Should be sorted descending by percent
        assert result[0]["label"] == "STOCK"

    def test_zero_total(self):
        result = compute_allocation({"STOCK": Decimal("0")}, Decimal("0"))
        assert result == []
