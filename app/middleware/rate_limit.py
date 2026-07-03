"""Redis-backed sliding window rate limiter."""

import logging
import time

import redis.asyncio as aioredis
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding window rate limiter keyed on client IP.

    Uses a Redis sorted set where each member is a request timestamp.
    The window is one minute; requests older than the window are pruned on each check.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip rate limiting for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)

        try:
            from app.core.redis import redis_pool

            client = aioredis.Redis(connection_pool=redis_pool)
            client_ip = request.client.host if request.client else "unknown"
            key = f"ratelimit:{client_ip}"
            now = time.time()
            window = 60.0

            pipe = client.pipeline()
            pipe.zremrangebyscore(key, 0, now - window)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, int(window) + 1)
            results = await pipe.execute()

            request_count = results[1]
            if request_count >= settings.rate_limit_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={"error": "Too many requests", "code": "AUTH_004"},
                )
            await client.aclose()
        except Exception:
            # If Redis is down, allow the request through rather than failing
            logger.warning("rate limiter unavailable, allowing request")

        return await call_next(request)
