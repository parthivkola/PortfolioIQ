from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.redis import get_redis
from app.market.service import MarketService

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/search")
async def search(
    q: str = Query(..., min_length=1),
    _user_id=Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    svc = MarketService(db, redis)
    results = await svc.search(q)
    return {"data": results}


@router.get("/quote/{symbol}")
async def get_quote(
    symbol: str,
    _user_id=Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    svc = MarketService(db, redis)
    return await svc.get_quote(symbol.upper())


@router.get("/history/{symbol}")
async def get_history(
    symbol: str,
    range: str = Query("1M", pattern="^(1M|3M|1Y|5Y)$"),
    _user_id=Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    svc = MarketService(db, redis)
    return await svc.get_history(symbol.upper(), range)
