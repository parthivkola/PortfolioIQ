"""Cache key constants and TTLs matching the invalidation matrix from the domain model."""


class CacheKeys:
    """Centralized cache key builders. Every cached read maps to exactly one pattern here."""

    @staticmethod
    def dashboard(user_id: str) -> str:
        return f"dashboard:{user_id}"

    @staticmethod
    def analytics(portfolio_id: str) -> str:
        return f"analytics:{portfolio_id}"

    @staticmethod
    def quote(symbol: str) -> str:
        return f"quote:{symbol}"


class InvalidationRules:
    """Maps write events to the cache keys they must invalidate.

    Reference: Domain Model doc, Section 4 -- Cache Invalidation Matrix.
    """

    @staticmethod
    def on_transaction(user_id: str, portfolio_id: str) -> list[str]:
        return [CacheKeys.dashboard(user_id), CacheKeys.analytics(portfolio_id)]

    @staticmethod
    def on_holding_correction(user_id: str, portfolio_id: str) -> list[str]:
        return [CacheKeys.dashboard(user_id), CacheKeys.analytics(portfolio_id)]

    @staticmethod
    def on_portfolio_change(user_id: str) -> list[str]:
        return [CacheKeys.dashboard(user_id)]

    @staticmethod
    def on_market_refresh(symbol: str) -> list[str]:
        return [CacheKeys.quote(symbol)]

    @staticmethod
    def on_daily_snapshot(portfolio_id: str) -> list[str]:
        return [CacheKeys.analytics(portfolio_id)]
