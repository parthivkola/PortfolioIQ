from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio import Portfolio


class PortfolioRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_user(self, user_id: UUID) -> list[Portfolio]:
        result = await self.db.execute(
            select(Portfolio)
            .where(Portfolio.user_id == user_id)
            .order_by(Portfolio.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, portfolio_id: UUID) -> Portfolio | None:
        result = await self.db.execute(select(Portfolio).where(Portfolio.id == portfolio_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, user_id: UUID, name: str) -> Portfolio | None:
        result = await self.db.execute(
            select(Portfolio).where(Portfolio.user_id == user_id, Portfolio.name == name)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: UUID, name: str) -> Portfolio:
        portfolio = Portfolio(user_id=user_id, name=name)
        self.db.add(portfolio)
        await self.db.flush()
        return portfolio

    async def update(self, portfolio: Portfolio, name: str) -> Portfolio:
        portfolio.name = name
        await self.db.flush()
        return portfolio

    async def delete(self, portfolio: Portfolio) -> None:
        await self.db.delete(portfolio)
        await self.db.flush()

    async def count_holdings(self, portfolio_id: UUID) -> int:
        from app.models.holding import Holding

        result = await self.db.execute(
            select(func.count()).where(Holding.portfolio_id == portfolio_id)
        )
        return result.scalar_one()
