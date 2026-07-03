"""Dashboard service -- aggregates portfolio, analytics, and market data into one response."""

import logging
from decimal import Decimal
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.keys import CacheKeys
from app.cache.manager import CacheManager
from app.core.config import settings
from app.repositories.holding import HoldingRepository
from app.repositories.market_snapshot import MarketSnapshotRepository
from app.repositories.transaction import TransactionRepository
from app.utils.decimal import safe_divide, to_str

logger = logging.getLogger(__name__)


class DashboardService:
    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.cache = CacheManager(redis_client)
        self.holding_repo = HoldingRepository(db)
        self.market_repo = MarketSnapshotRepository(db)
        self.transaction_repo = TransactionRepository(db)

    async def get_dashboard(self, user_id: UUID, portfolio_ids: list[UUID]) -> dict:
        cache_key = CacheKeys.dashboard(str(user_id))
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        total_current = Decimal("0")
        total_invested = Decimal("0")
        holdings_data: list[dict] = []
        asset_values: dict[str, Decimal] = {}

        for pid in portfolio_ids:
            holdings = await self.holding_repo.list_by_portfolio(pid)
            for h in holdings:
                price_row = await self.market_repo.get_latest_by_symbol(h.symbol)
                current_price = price_row.market_price if price_row else h.average_buy_price
                value = h.quantity * current_price
                invested = h.quantity * h.average_buy_price

                total_current += value
                total_invested += invested

                pnl_pct = safe_divide(
                    (current_price - h.average_buy_price) * 100,
                    h.average_buy_price,
                )
                holdings_data.append(
                    {
                        "symbol": h.symbol,
                        "value": value,
                        "pnl_percent": pnl_pct,
                    }
                )

                asset_key = h.asset_type.value
                asset_values[asset_key] = asset_values.get(asset_key, Decimal("0")) + value

        overall_gain = total_current - total_invested
        overall_pct = (
            safe_divide(overall_gain * 100, total_invested) if total_invested > 0 else Decimal("0")
        )

        # Top gainers and losers
        sorted_by_pnl = sorted(holdings_data, key=lambda x: x["pnl_percent"], reverse=True)
        top_gainers = [
            {"symbol": h["symbol"], "percent": to_str(h["pnl_percent"], 1)}
            for h in sorted_by_pnl[:3]
            if h["pnl_percent"] > 0
        ]
        top_losers = [
            {"symbol": h["symbol"], "percent": to_str(h["pnl_percent"], 1)}
            for h in reversed(sorted_by_pnl)
            if h["pnl_percent"] < 0
        ][:3]

        # Recent transactions
        recent_txns = []
        for pid in portfolio_ids[:3]:
            txns = await self.transaction_repo.get_recent_for_portfolio(pid, limit=5)
            for t in txns:
                holding = await self.holding_repo.get_by_id(t.holding_id)
                recent_txns.append(
                    {
                        "id": str(t.id),
                        "transaction_type": t.transaction_type.value,
                        "symbol": holding.symbol if holding else "UNKNOWN",
                        "timestamp": t.timestamp.isoformat(),
                    }
                )

        # Asset allocation
        allocation = []
        for asset_type, val in asset_values.items():
            pct = safe_divide(val * 100, total_current) if total_current > 0 else Decimal("0")
            allocation.append({"asset_type": asset_type, "percent": to_str(pct, 1)})

        result = {
            "current_value": to_str(total_current),
            "total_invested": to_str(total_invested),
            "todays_gain": {"amount": "0.00", "percent": "0.00"},  # requires previous close data
            "overall_gain": {"amount": to_str(overall_gain), "percent": to_str(overall_pct)},
            "top_gainers": top_gainers,
            "top_losers": top_losers,
            "recent_transactions": recent_txns[:5],
            "asset_allocation": allocation,
        }

        await self.cache.set(cache_key, result, settings.cache_ttl_dashboard)
        return result
