"""APScheduler setup for background jobs."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.tasks.market_refresh import refresh_market_prices
from app.tasks.snapshot import generate_daily_snapshots

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def configure_scheduler() -> None:
    """Register all background jobs. Call once during app startup."""

    # Market price refresh -- every 60 seconds
    scheduler.add_job(
        refresh_market_prices,
        trigger=IntervalTrigger(seconds=60),
        id="market_refresh",
        name="Market Price Refresh",
        replace_existing=True,
    )

    # Daily portfolio snapshot -- 00:05 IST (18:35 UTC previous day)
    scheduler.add_job(
        generate_daily_snapshots,
        trigger=CronTrigger(hour=18, minute=35),
        id="daily_snapshot",
        name="Daily Portfolio Snapshot",
        replace_existing=True,
    )

    logger.info("scheduler configured with %d jobs", len(scheduler.get_jobs()))
