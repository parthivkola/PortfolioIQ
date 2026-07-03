from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio_snapshot import PortfolioSnapshot


class PortfolioSnapshotRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_latest(self, portfolio_id: UUID) -> PortfolioSnapshot | None:
        result = await self.db.execute(
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.portfolio_id == portfolio_id)
            .order_by(PortfolioSnapshot.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_by_portfolio(
        self,
        portfolio_id: UUID,
        limit: int = 365,
    ) -> list[PortfolioSnapshot]:
        result = await self.db.execute(
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.portfolio_id == portfolio_id)
            .order_by(PortfolioSnapshot.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(
        self,
        portfolio_id: UUID,
        portfolio_value: Decimal,
        invested_value: Decimal,
        pnl: Decimal,
    ) -> PortfolioSnapshot:
        snapshot = PortfolioSnapshot(
            portfolio_id=portfolio_id,
            portfolio_value=portfolio_value,
            invested_value=invested_value,
            pnl=pnl,
        )
        self.db.add(snapshot)
        await self.db.flush()
        return snapshot
