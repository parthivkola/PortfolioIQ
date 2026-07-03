from datetime import datetime

from pydantic import BaseModel, Field

from app.models.holding import AssetType


class HoldingCreate(BaseModel):
    portfolio_id: str
    asset_type: AssetType
    symbol: str = Field(..., min_length=1, max_length=40)


class HoldingUpdate(BaseModel):
    quantity: str
    average_buy_price: str


class HoldingResponse(BaseModel):
    id: str
    portfolio_id: str
    asset_type: AssetType
    symbol: str
    quantity: str
    average_buy_price: str

    model_config = {"from_attributes": True}


class HoldingDetailResponse(HoldingResponse):
    current_price: str | None = None
    current_value: str | None = None
    pnl: str | None = None
    pnl_percent: str | None = None
    updated_at: datetime | None = None
