from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction, TransactionType


class TransactionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_holding(
        self,
        holding_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Transaction], int]:
        count_result = await self.db.execute(
            select(func.count()).where(Transaction.holding_id == holding_id)
        )
        total = count_result.scalar_one()

        result = await self.db.execute(
            select(Transaction)
            .where(Transaction.holding_id == holding_id)
            .order_by(Transaction.timestamp.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total

    async def list_by_portfolio(
        self,
        portfolio_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Transaction], int]:
        from app.models.holding import Holding

        count_result = await self.db.execute(
            select(func.count())
            .select_from(Transaction)
            .join(Holding, Transaction.holding_id == Holding.id)
            .where(Holding.portfolio_id == portfolio_id)
        )
        total = count_result.scalar_one()

        result = await self.db.execute(
            select(Transaction)
            .join(Holding, Transaction.holding_id == Holding.id)
            .where(Holding.portfolio_id == portfolio_id)
            .order_by(Transaction.timestamp.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total

    async def list_all_for_holding(self, holding_id: UUID) -> list[Transaction]:
        """All transactions for a holding, oldest first (for analytics)."""
        result = await self.db.execute(
            select(Transaction)
            .where(Transaction.holding_id == holding_id)
            .order_by(Transaction.timestamp.asc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        holding_id: UUID,
        transaction_type: TransactionType,
        quantity: Decimal,
        price: Decimal,
        timestamp: datetime,
    ) -> Transaction:
        txn = Transaction(
            holding_id=holding_id,
            transaction_type=transaction_type,
            quantity=quantity,
            price=price,
            timestamp=timestamp,
        )
        self.db.add(txn)
        await self.db.flush()
        return txn

    async def get_sells_for_holding(self, holding_id: UUID) -> list[Transaction]:
        """All SELL transactions for realized P&L calculation."""
        result = await self.db.execute(
            select(Transaction)
            .where(
                Transaction.holding_id == holding_id,
                Transaction.transaction_type == TransactionType.SELL,
            )
            .order_by(Transaction.timestamp.asc())
        )
        return list(result.scalars().all())

    async def get_dividends_for_holding(self, holding_id: UUID) -> list[Transaction]:
        result = await self.db.execute(
            select(Transaction)
            .where(
                Transaction.holding_id == holding_id,
                Transaction.transaction_type == TransactionType.DIVIDEND,
            )
            .order_by(Transaction.timestamp.asc())
        )
        return list(result.scalars().all())

    async def get_recent_for_portfolio(
        self, portfolio_id: UUID, limit: int = 5
    ) -> list[Transaction]:
        from app.models.holding import Holding

        result = await self.db.execute(
            select(Transaction)
            .join(Holding, Transaction.holding_id == Holding.id)
            .where(Holding.portfolio_id == portfolio_id)
            .order_by(Transaction.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
