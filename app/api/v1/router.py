from fastapi import APIRouter

from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.health import router as health_router
from app.api.v1.holdings import router as holdings_router
from app.api.v1.market import router as market_router
from app.api.v1.portfolio import router as portfolio_router
from app.api.v1.transactions import router as transactions_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth_router)
v1_router.include_router(portfolio_router)
v1_router.include_router(holdings_router)
v1_router.include_router(transactions_router)
v1_router.include_router(dashboard_router)
v1_router.include_router(analytics_router)
v1_router.include_router(market_router)
v1_router.include_router(health_router)
