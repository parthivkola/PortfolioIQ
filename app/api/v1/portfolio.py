from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.portfolio.service import PortfolioService
from app.schemas.portfolio import PortfolioCreate, PortfolioResponse, PortfolioUpdate

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("", response_model=list[PortfolioResponse])
async def list_portfolios(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = PortfolioService(db)
    portfolios = await svc.list_portfolios(user_id)
    return [
        PortfolioResponse(id=str(p.id), name=p.name, created_at=p.created_at) for p in portfolios
    ]


@router.post("", response_model=PortfolioResponse, status_code=201)
async def create_portfolio(
    body: PortfolioCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = PortfolioService(db)
    p = await svc.create_portfolio(user_id, body.name)
    return PortfolioResponse(id=str(p.id), name=p.name, created_at=p.created_at)


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: UUID,
    body: PortfolioUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = PortfolioService(db)
    p = await svc.update_portfolio(portfolio_id, user_id, body.name)
    return PortfolioResponse(id=str(p.id), name=p.name, created_at=p.created_at)


@router.delete("/{portfolio_id}", status_code=204)
async def delete_portfolio(
    portfolio_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = PortfolioService(db)
    await svc.delete_portfolio(portfolio_id, user_id)
