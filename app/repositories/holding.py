from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holding import AssetType, Holding


class HoldingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_portfolio(
        self,
        portfolio_id: UUID,
        asset_type: AssetType | None = None,
    ) -> list[Holding]:
        query = select(Holding).where(Holding.portfolio_id == portfolio_id)
        if asset_type:
            query = query.where(Holding.asset_type == asset_type)
        result = await self.db.execute(query.order_by(Holding.symbol))
        return list(result.scalars().all())

    async def get_by_id(self, holding_id: UUID) -> Holding | None:
        result = await self.db.execute(select(Holding).where(Holding.id == holding_id))
        return result.scalar_one_or_none()

    async def get_by_symbol(self, portfolio_id: UUID, symbol: str) -> Holding | None:
        result = await self.db.execute(
            select(Holding).where(Holding.portfolio_id == portfolio_id, Holding.symbol == symbol)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        portfolio_id: UUID,
        asset_type: AssetType,
        symbol: str,
    ) -> Holding:
        holding = Holding(
            portfolio_id=portfolio_id,
            asset_type=asset_type,
            symbol=symbol.upper(),
            quantity=Decimal("0"),
            average_buy_price=Decimal("0"),
        )
        self.db.add(holding)
        await self.db.flush()
        return holding

    async def update(
        self,
        holding: Holding,
        quantity: Decimal | None = None,
        average_buy_price: Decimal | None = None,
    ) -> Holding:
        if quantity is not None:
            holding.quantity = quantity
        if average_buy_price is not None:
            holding.average_buy_price = average_buy_price
        await self.db.flush()
        return holding

    async def delete(self, holding: Holding) -> None:
        await self.db.delete(holding)
        await self.db.flush()

    async def get_all_symbols(self) -> list[str]:
        """Return distinct symbols across all holdings (for market refresh job)."""
        result = await self.db.execute(select(Holding.symbol).distinct())
        return [row[0] for row in result.all()]
