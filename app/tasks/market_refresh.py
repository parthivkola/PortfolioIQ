"""Background job: refresh market quotes for all held symbols."""

import logging
from datetime import UTC, datetime

from app.core.database import async_session_factory
from app.market.provider import YahooFinanceProvider
from app.repositories.holding import HoldingRepository
from app.repositories.market_snapshot import MarketSnapshotRepository

logger = logging.getLogger(__name__)
provider = YahooFinanceProvider()


async def refresh_market_prices() -> None:
    """Pull latest quotes for every symbol held across all portfolios.

    Runs on a 60-second interval via the scheduler. Each quote is written
    to both the MarketSnapshot table and the Redis quote cache.
    """
    logger.info("market refresh job started")

    async with async_session_factory() as db:
        holding_repo = HoldingRepository(db)
        snapshot_repo = MarketSnapshotRepository(db)

        symbols = await holding_repo.get_all_symbols()
        if not symbols:
            logger.info("no symbols to refresh")
            return

        updated = 0
        for symbol in symbols:
            try:
                result = await provider.get_quote(symbol)
                if result and result.get("price"):
                    now = datetime.now(UTC)
                    await snapshot_repo.upsert(symbol, result["price"], now)
                    updated += 1
            except Exception:
                logger.exception("failed to refresh quote for %s", symbol)

        await db.commit()
        logger.info("market refresh completed: %d/%d symbols updated", updated, len(symbols))
