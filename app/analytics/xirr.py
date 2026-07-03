"""XIRR solver using Newton-Raphson with bisection fallback.

Finds the annualized discount rate r such that:
  NPV(r) = sum(CF_i / (1+r)^t_i) = 0
where t_i = (date_i - date_0) / 365
"""

from datetime import date, datetime

from app.exceptions import XIRRConvergenceError


def xirr(
    cash_flows: list[float],
    dates: list[date | datetime],
    guess: float = 0.1,
    tol: float = 1e-6,
    max_iter: int = 100,
) -> float:
    """Compute XIRR for a series of irregular cash flows.

    Args:
        cash_flows: Signed amounts (negative = outflow/BUY, positive = inflow/SELL/current value).
        dates: Corresponding dates for each cash flow.
        guess: Initial rate estimate.
        tol: Convergence tolerance.
        max_iter: Maximum Newton-Raphson iterations before fallback.

    Returns:
        Annualized return rate as a float.

    Raises:
        XIRRConvergenceError: If the series is unsolvable or doesn't converge.
    """
    if len(cash_flows) < 2:
        raise XIRRConvergenceError("XIRR requires at least two cash flows")

    # All flows same sign means no root exists
    signs = {cf > 0 for cf in cash_flows if cf != 0}
    if len(signs) <= 1:
        raise XIRRConvergenceError("All cash flows have the same sign; no real root exists")

    d0 = _to_date(dates[0])
    t = [(_to_date(d) - d0).days / 365.0 for d in dates]

    # Try Newton-Raphson first
    result = _newton_raphson(cash_flows, t, guess, tol, max_iter)
    if result is not None:
        return result

    # Fall back to bisection over a bounded range
    result = _bisection(cash_flows, t, lo=-0.99, hi=10.0, tol=tol, max_iter=max_iter * 10)
    if result is not None:
        return result

    raise XIRRConvergenceError("XIRR did not converge")


def _newton_raphson(
    cash_flows: list[float],
    t: list[float],
    guess: float,
    tol: float,
    max_iter: int,
) -> float | None:
    r = guess
    for _ in range(max_iter):
        npv = sum(cf / (1 + r) ** ti for cf, ti in zip(cash_flows, t, strict=False))
        dnpv = sum(-ti * cf / (1 + r) ** (ti + 1) for cf, ti in zip(cash_flows, t, strict=False))
        if abs(dnpv) < 1e-12:
            return None  # derivative too small, try bisection
        r_next = r - npv / dnpv
        if abs(r_next - r) < tol:
            return r_next
        r = r_next
    return None  # didn't converge


def _bisection(
    cash_flows: list[float],
    t: list[float],
    lo: float,
    hi: float,
    tol: float,
    max_iter: int,
) -> float | None:
    def npv_at(r: float) -> float:
        return sum(cf / (1 + r) ** ti for cf, ti in zip(cash_flows, t, strict=False))

    npv_lo = npv_at(lo)
    npv_hi = npv_at(hi)
    if npv_lo * npv_hi > 0:
        return None  # no sign change in range

    for _ in range(max_iter):
        mid = (lo + hi) / 2
        npv_mid = npv_at(mid)
        if abs(npv_mid) < tol or (hi - lo) / 2 < tol:
            return mid
        if npv_mid * npv_lo < 0:
            hi = mid
        else:
            lo = mid
            npv_lo = npv_mid
    return None


def _to_date(d: date | datetime) -> date:
    if isinstance(d, datetime):
        return d.date()
    return d
