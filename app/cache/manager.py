"""Cache manager with get/set/invalidate helpers and Decimal-safe JSON serialization."""

import json
import logging
from decimal import Decimal

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


class CacheManager:
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    async def get(self, key: str) -> dict | None:
        raw = await self.redis.get(key)
        if raw:
            return json.loads(raw)
        return None

    async def set(self, key: str, data: dict, ttl: int) -> None:
        serialized = json.dumps(data, cls=DecimalEncoder)
        await self.redis.set(key, serialized, ex=ttl)

    async def invalidate(self, keys: list[str]) -> None:
        if keys:
            await self.redis.delete(*keys)
            logger.debug("invalidated cache keys: %s", keys)

    async def invalidate_pattern(self, pattern: str) -> None:
        """Delete all keys matching a glob pattern. Use sparingly."""
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break
