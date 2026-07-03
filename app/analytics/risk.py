"""Portfolio risk metrics: volatility, concentration, beta."""

import math


def volatility_from_returns(daily_returns: list[float]) -> float | None:
    """Annualized volatility from a series of daily portfolio returns.

    Uses 30-day rolling window standard deviation, annualized by sqrt(252).
    Returns None if insufficient data points.
    """
    if len(daily_returns) < 2:
        return None

    n = min(len(daily_returns), 30)
    recent = daily_returns[-n:]
    mean = sum(recent) / len(recent)
    variance = sum((r - mean) ** 2 for r in recent) / (len(recent) - 1)
    daily_vol = math.sqrt(variance)
    return daily_vol * math.sqrt(252)


def concentration_risk(largest_weight: float) -> str:
    """Classify concentration risk based on the largest holding's weight."""
    if largest_weight >= 0.5:
        return "HIGH"
    if largest_weight >= 0.25:
        return "MODERATE"
    return "LOW"


def beta(portfolio_returns: list[float], benchmark_returns: list[float]) -> float | None:
    """Compute beta of portfolio against a benchmark.

    Beta = Cov(portfolio, benchmark) / Var(benchmark)
    Returns None if insufficient data.
    """
    if len(portfolio_returns) < 5 or len(benchmark_returns) < 5:
        return None

    n = min(len(portfolio_returns), len(benchmark_returns))
    pr = portfolio_returns[-n:]
    br = benchmark_returns[-n:]

    mean_p = sum(pr) / n
    mean_b = sum(br) / n

    covariance = sum((p - mean_p) * (b - mean_b) for p, b in zip(pr, br, strict=False)) / (n - 1)
    var_b = sum((b - mean_b) ** 2 for b in br) / (n - 1)

    if var_b == 0:
        return None

    return round(covariance / var_b, 4)
