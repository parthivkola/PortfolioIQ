from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.models.holding import AssetType
from app.portfolio.service import PortfolioService
from app.schemas.holding import HoldingCreate, HoldingResponse, HoldingUpdate

router = APIRouter(prefix="/holdings", tags=["holdings"])


@router.get("", response_model=list[HoldingResponse])
async def list_holdings(
    portfolio_id: UUID = Query(...),
    asset_type: AssetType | None = Query(None),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = PortfolioService(db)
    holdings = await svc.list_holdings(portfolio_id, user_id, asset_type)
    return [
        HoldingResponse(
            id=str(h.id),
            portfolio_id=str(h.portfolio_id),
            asset_type=h.asset_type,
            symbol=h.symbol,
            quantity=str(h.quantity),
            average_buy_price=str(h.average_buy_price),
        )
        for h in holdings
    ]


@router.post("", response_model=HoldingResponse, status_code=201)
async def create_holding(
    body: HoldingCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = PortfolioService(db)
    h = await svc.create_holding(UUID(body.portfolio_id), user_id, body.asset_type, body.symbol)
    return HoldingResponse(
        id=str(h.id),
        portfolio_id=str(h.portfolio_id),
        asset_type=h.asset_type,
        symbol=h.symbol,
        quantity=str(h.quantity),
        average_buy_price=str(h.average_buy_price),
    )


@router.put("/{holding_id}", response_model=HoldingResponse)
async def update_holding(
    holding_id: UUID,
    body: HoldingUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = PortfolioService(db)
    h = await svc.update_holding(
        holding_id, user_id, Decimal(body.quantity), Decimal(body.average_buy_price)
    )
    return HoldingResponse(
        id=str(h.id),
        portfolio_id=str(h.portfolio_id),
        asset_type=h.asset_type,
        symbol=h.symbol,
        quantity=str(h.quantity),
        average_buy_price=str(h.average_buy_price),
    )


@router.delete("/{holding_id}", status_code=204)
async def delete_holding(
    holding_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = PortfolioService(db)
    await svc.delete_holding(holding_id, user_id)
