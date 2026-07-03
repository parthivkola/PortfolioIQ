"""Background job: generate daily portfolio snapshots."""

import logging
from decimal import Decimal

from app.core.database import async_session_factory
from app.repositories.holding import HoldingRepository
from app.repositories.market_snapshot import MarketSnapshotRepository
from app.repositories.portfolio_snapshot import PortfolioSnapshotRepository

logger = logging.getLogger(__name__)


async def generate_daily_snapshots() -> None:
    """Compute and persist a PortfolioSnapshot for every portfolio.

    Runs daily at 00:05 IST. Each snapshot records the portfolio's current
    market value, invested capital, and P&L at the snapshot moment.
    """
    logger.info("daily snapshot job started")

    async with async_session_factory() as db:
        from sqlalchemy import select

        from app.models.portfolio import Portfolio

        result = await db.execute(select(Portfolio))
        portfolios = list(result.scalars().all())

        holding_repo = HoldingRepository(db)
        market_repo = MarketSnapshotRepository(db)
        snapshot_repo = PortfolioSnapshotRepository(db)

        created = 0
        for portfolio in portfolios:
            try:
                holdings = await holding_repo.list_by_portfolio(portfolio.id)
                if not holdings:
                    continue

                total_value = Decimal("0")
                total_invested = Decimal("0")

                for h in holdings:
                    price_row = await market_repo.get_latest_by_symbol(h.symbol)
                    price = price_row.market_price if price_row else h.average_buy_price
                    total_value += h.quantity * price
                    total_invested += h.quantity * h.average_buy_price

                pnl = total_value - total_invested
                await snapshot_repo.create(portfolio.id, total_value, total_invested, pnl)
                created += 1
            except Exception:
                logger.exception("snapshot failed for portfolio %s", portfolio.id)

        await db.commit()
        logger.info("daily snapshot completed: %d portfolios processed", created)
