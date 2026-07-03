"""Market data service with cache-through pattern.

Checks Redis first, falls back to provider, stores result in both Redis and Postgres.
On provider failure, serves stale cache if available.
"""

import json
import logging
from datetime import UTC, datetime
from decimal import Decimal

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.keys import CacheKeys
from app.core.config import settings
from app.exceptions import MarketProviderError
from app.market.provider import MarketDataProvider, YahooFinanceProvider
from app.repositories.market_snapshot import MarketSnapshotRepository

logger = logging.getLogger(__name__)


class MarketService:
    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis):
        self.db = db
        self.redis = redis_client
        self.snapshot_repo = MarketSnapshotRepository(db)
        self.provider: MarketDataProvider = YahooFinanceProvider()

    async def get_quote(self, symbol: str) -> dict:
        """Get the latest quote, preferring cache, falling back to provider."""
        cache_key = CacheKeys.quote(symbol)

        # Try cache
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        # Cache miss -- hit provider
        result = await self.provider.get_quote(symbol)
        if result:
            now = datetime.now(UTC)
            await self.snapshot_repo.upsert(symbol, result["price"], now)

            response = {
                "symbol": symbol,
                "price": str(result["price"]),
                "as_of": result["as_of"],
                "source": "provider",
            }
            await self.redis.set(cache_key, json.dumps(response), ex=settings.cache_ttl_quote)
            return response

        # Provider failed -- try stale DB data
        db_row = await self.snapshot_repo.get_latest_by_symbol(symbol)
        if db_row:
            logger.warning("serving stale quote for %s from DB", symbol)
            return {
                "symbol": symbol,
                "price": str(db_row.market_price),
                "as_of": db_row.timestamp.isoformat(),
                "source": "stale-cache",
            }

        raise MarketProviderError()

    async def search(self, query: str) -> list[dict]:
        return await self.provider.search(query)

    async def get_history(self, symbol: str, range_str: str) -> dict:
        points = await self.provider.get_history(symbol, range_str)
        return {"symbol": symbol, "range": range_str, "points": points}

    async def get_latest_price(self, symbol: str) -> Decimal | None:
        """Convenience method for internal use (analytics, dashboard)."""
        cache_key = CacheKeys.quote(symbol)
        cached = await self.redis.get(cache_key)
        if cached:
            data = json.loads(cached)
            return Decimal(data["price"])

        db_row = await self.snapshot_repo.get_latest_by_symbol(symbol)
        if db_row:
            return db_row.market_price
        return None
