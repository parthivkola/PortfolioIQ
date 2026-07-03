from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market_snapshot import MarketSnapshot


class MarketSnapshotRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_latest_by_symbol(self, symbol: str) -> MarketSnapshot | None:
        result = await self.db.execute(
            select(MarketSnapshot)
            .where(MarketSnapshot.symbol == symbol)
            .order_by(MarketSnapshot.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_history(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> list[MarketSnapshot]:
        result = await self.db.execute(
            select(MarketSnapshot)
            .where(
                MarketSnapshot.symbol == symbol,
                MarketSnapshot.timestamp >= start,
                MarketSnapshot.timestamp <= end,
            )
            .order_by(MarketSnapshot.timestamp.asc())
        )
        return list(result.scalars().all())

    async def upsert(self, symbol: str, price: Decimal, timestamp: datetime) -> MarketSnapshot:
        """Insert a new snapshot. Duplicates on (symbol, timestamp) are skipped."""
        existing = await self.db.execute(
            select(MarketSnapshot).where(
                MarketSnapshot.symbol == symbol, MarketSnapshot.timestamp == timestamp
            )
        )
        row = existing.scalar_one_or_none()
        if row:
            row.market_price = price
            await self.db.flush()
            return row

        snapshot = MarketSnapshot(symbol=symbol, market_price=price, timestamp=timestamp)
        self.db.add(snapshot)
        await self.db.flush()
        return snapshot
