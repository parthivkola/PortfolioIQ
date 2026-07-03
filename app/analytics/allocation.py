"""Portfolio allocation analysis and diversification scoring."""

from decimal import Decimal

from app.utils.decimal import safe_divide


def diversification_score(weights: list[Decimal]) -> Decimal:
    """Compute 1 - HHI (Herfindahl-Hirschman Index).

    0 = fully concentrated in one asset
    Approaching 1 = maximally diversified
    """
    if not weights:
        return Decimal("0")
    hhi = sum(w**2 for w in weights)
    return Decimal("1") - hhi


def compute_allocation(
    holdings_values: dict[str, Decimal],
    total_value: Decimal,
) -> list[dict[str, str]]:
    """Break down portfolio by a grouping key (asset type, sector, etc.).

    Args:
        holdings_values: Mapping of group label -> total value in that group.
        total_value: Sum across all groups.

    Returns:
        List of {"label": ..., "percent": ...} dicts sorted by weight descending.
    """
    if total_value <= 0:
        return []

    result = []
    for label, value in holdings_values.items():
        pct = safe_divide(value * 100, total_value)
        result.append({"label": label, "percent": str(pct.quantize(Decimal("0.1")))})

    return sorted(result, key=lambda x: Decimal(x["percent"]), reverse=True)
