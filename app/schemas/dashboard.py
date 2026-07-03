from pydantic import BaseModel


class GainSummary(BaseModel):
    amount: str
    percent: str


class TopMover(BaseModel):
    symbol: str
    percent: str


class RecentTransaction(BaseModel):
    id: str
    transaction_type: str
    symbol: str
    timestamp: str


class AllocationSlice(BaseModel):
    asset_type: str | None = None
    sector: str | None = None
    percent: str


class DashboardResponse(BaseModel):
    current_value: str
    total_invested: str
    todays_gain: GainSummary
    overall_gain: GainSummary
    top_gainers: list[TopMover]
    top_losers: list[TopMover]
    recent_transactions: list[RecentTransaction]
    asset_allocation: list[AllocationSlice]
