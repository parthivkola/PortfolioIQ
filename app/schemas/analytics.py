from pydantic import BaseModel


class PerformanceResponse(BaseModel):
    xirr: str | None
    cagr: str | None
    absolute_return_percent: str | None
    unrealized_pnl: str
    realized_pnl: str
    daily_pnl: str


class AllocationEntry(BaseModel):
    asset_type: str | None = None
    bucket: str | None = None
    sector: str | None = None
    percent: str


class LargestHolding(BaseModel):
    symbol: str
    percent: str


class AllocationResponse(BaseModel):
    by_asset_type: list[AllocationEntry]
    by_market_cap: list[AllocationEntry]
    by_sector: list[AllocationEntry]
    diversification_score: str
    largest_holding: LargestHolding | None


class RiskResponse(BaseModel):
    volatility_30d: str | None
    concentration_risk: str
    beta_vs_nifty50: str | None


class TaxLossCandidate(BaseModel):
    holding_id: str
    symbol: str
    unrealized_loss: str


class TaxResponse(BaseModel):
    dividend_income: str
    tax_loss_opportunities: list[TaxLossCandidate]
