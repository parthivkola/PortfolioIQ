from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.service import AnalyticsService
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.portfolio.service import PortfolioService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/performance")
async def get_performance(
    portfolio_id: UUID = Query(...),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    portfolio_svc = PortfolioService(db)
    await portfolio_svc.get_portfolio(portfolio_id, user_id)

    svc = AnalyticsService(db)
    return await svc.get_performance(portfolio_id)


@router.get("/allocation")
async def get_allocation(
    portfolio_id: UUID = Query(...),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    portfolio_svc = PortfolioService(db)
    await portfolio_svc.get_portfolio(portfolio_id, user_id)

    svc = AnalyticsService(db)
    return await svc.get_allocation(portfolio_id)


@router.get("/risk")
async def get_risk(
    portfolio_id: UUID = Query(...),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    portfolio_svc = PortfolioService(db)
    await portfolio_svc.get_portfolio(portfolio_id, user_id)

    svc = AnalyticsService(db)
    return await svc.get_risk(portfolio_id)


@router.get("/tax")
async def get_tax(
    portfolio_id: UUID = Query(...),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    portfolio_svc = PortfolioService(db)
    await portfolio_svc.get_portfolio(portfolio_id, user_id)

    svc = AnalyticsService(db)
    return await svc.get_tax(portfolio_id)
