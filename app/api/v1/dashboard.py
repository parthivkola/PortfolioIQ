from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.redis import get_redis
from app.portfolio.service import PortfolioService
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard(
    portfolio_id: UUID | None = Query(None, description="Optional, omit for all portfolios"),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    portfolio_svc = PortfolioService(db)

    if portfolio_id:
        await portfolio_svc.get_portfolio(portfolio_id, user_id)
        portfolio_ids = [portfolio_id]
    else:
        portfolios = await portfolio_svc.list_portfolios(user_id)
        portfolio_ids = [p.id for p in portfolios]

    svc = DashboardService(db, redis)
    return await svc.get_dashboard(user_id, portfolio_ids)
