import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    HoldingAlreadyExistsError,
    HoldingNotFoundError,
    OverSellError,
    PortfolioAccessDeniedError,
    PortfolioHasHoldingsError,
    PortfolioNameConflictError,
    PortfolioNotFoundError,
)
from app.models.holding import AssetType, Holding
from app.models.portfolio import Portfolio
from app.models.transaction import Transaction, TransactionType
from app.repositories.holding import HoldingRepository
from app.repositories.portfolio import PortfolioRepository
from app.repositories.transaction import TransactionRepository

logger = logging.getLogger(__name__)


class PortfolioService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.portfolio_repo = PortfolioRepository(db)
        self.holding_repo = HoldingRepository(db)
        self.transaction_repo = TransactionRepository(db)

    # -- Portfolio CRUD --

    async def list_portfolios(self, user_id: UUID) -> list[Portfolio]:
        return await self.portfolio_repo.list_by_user(user_id)

    async def get_portfolio(self, portfolio_id: UUID, user_id: UUID) -> Portfolio:
        portfolio = await self.portfolio_repo.get_by_id(portfolio_id)
        if not portfolio:
            raise PortfolioNotFoundError()
        if portfolio.user_id != user_id:
            raise PortfolioAccessDeniedError()
        return portfolio

    async def create_portfolio(self, user_id: UUID, name: str) -> Portfolio:
        existing = await self.portfolio_repo.get_by_name(user_id, name)
        if existing:
            raise PortfolioNameConflictError()
        return await self.portfolio_repo.create(user_id, name)

    async def update_portfolio(self, portfolio_id: UUID, user_id: UUID, name: str) -> Portfolio:
        portfolio = await self.get_portfolio(portfolio_id, user_id)
        existing = await self.portfolio_repo.get_by_name(user_id, name)
        if existing and existing.id != portfolio_id:
            raise PortfolioNameConflictError()
        return await self.portfolio_repo.update(portfolio, name)

    async def delete_portfolio(self, portfolio_id: UUID, user_id: UUID) -> None:
        portfolio = await self.get_portfolio(portfolio_id, user_id)
        count = await self.portfolio_repo.count_holdings(portfolio_id)
        if count > 0:
            raise PortfolioHasHoldingsError()
        await self.portfolio_repo.delete(portfolio)

    # -- Holding CRUD --

    async def list_holdings(
        self,
        portfolio_id: UUID,
        user_id: UUID,
        asset_type: AssetType | None = None,
    ) -> list[Holding]:
        await self.get_portfolio(portfolio_id, user_id)  # ownership check
        return await self.holding_repo.list_by_portfolio(portfolio_id, asset_type)

    async def get_holding(self, holding_id: UUID, user_id: UUID) -> Holding:
        holding = await self.holding_repo.get_by_id(holding_id)
        if not holding:
            raise HoldingNotFoundError()
        await self.get_portfolio(holding.portfolio_id, user_id)  # ownership check
        return holding

    async def create_holding(
        self, portfolio_id: UUID, user_id: UUID, asset_type: AssetType, symbol: str
    ) -> Holding:
        await self.get_portfolio(portfolio_id, user_id)
        existing = await self.holding_repo.get_by_symbol(portfolio_id, symbol.upper())
        if existing:
            raise HoldingAlreadyExistsError()
        return await self.holding_repo.create(portfolio_id, asset_type, symbol)

    async def update_holding(
        self,
        holding_id: UUID,
        user_id: UUID,
        quantity: Decimal,
        average_buy_price: Decimal,
    ) -> Holding:
        holding = await self.get_holding(holding_id, user_id)
        logger.info("manual holding correction: %s", holding_id)
        return await self.holding_repo.update(holding, quantity, average_buy_price)

    async def delete_holding(self, holding_id: UUID, user_id: UUID) -> None:
        holding = await self.get_holding(holding_id, user_id)
        if holding.quantity > 0:
            raise PortfolioHasHoldingsError()
        await self.holding_repo.delete(holding)

    # -- Transaction processing (the core write path) --

    async def process_transaction(
        self,
        holding_id: UUID,
        user_id: UUID,
        transaction_type: TransactionType,
        quantity: Decimal,
        price: Decimal,
        timestamp,
    ) -> Transaction:
        holding = await self.get_holding(holding_id, user_id)

        if transaction_type == TransactionType.BUY:
            self._apply_buy(holding, quantity, price)
        elif transaction_type == TransactionType.SELL:
            self._apply_sell(holding, quantity)
        elif transaction_type == TransactionType.DIVIDEND:
            pass  # no holding state change
        elif transaction_type == TransactionType.BONUS:
            self._apply_bonus(holding, quantity)
        elif transaction_type == TransactionType.SPLIT:
            self._apply_split(holding, quantity)

        await self.holding_repo.update(holding, holding.quantity, holding.average_buy_price)
        txn = await self.transaction_repo.create(
            holding_id=holding_id,
            transaction_type=transaction_type,
            quantity=quantity,
            price=price,
            timestamp=timestamp,
        )
        logger.info(
            "transaction processed: %s %s for holding %s",
            transaction_type,
            quantity,
            holding_id,
        )
        return txn

    def _apply_buy(self, holding: Holding, qty: Decimal, price: Decimal) -> None:
        """BUY: increase quantity and recalculate weighted average buy price."""
        old_qty = holding.quantity
        old_avg = holding.average_buy_price
        new_qty = old_qty + qty
        if new_qty > 0:
            holding.average_buy_price = ((old_qty * old_avg) + (qty * price)) / new_qty
        holding.quantity = new_qty

    def _apply_sell(self, holding: Holding, qty: Decimal) -> None:
        """SELL: reduce quantity, keep average buy price unchanged."""
        if qty > holding.quantity:
            raise OverSellError()
        holding.quantity = holding.quantity - qty

    def _apply_bonus(self, holding: Holding, ratio: Decimal) -> None:
        """BONUS: increase qty by ratio, redistribute cost basis."""
        holding.quantity = holding.quantity * (1 + ratio)
        if (1 + ratio) != 0:
            holding.average_buy_price = holding.average_buy_price / (1 + ratio)

    def _apply_split(self, holding: Holding, ratio: Decimal) -> None:
        """SPLIT: multiply qty by ratio, divide avg price by ratio."""
        holding.quantity = holding.quantity * ratio
        if ratio != 0:
            holding.average_buy_price = holding.average_buy_price / ratio

    # -- Transaction listing --

    async def list_transactions(
        self,
        user_id: UUID,
        holding_id: UUID | None = None,
        portfolio_id: UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Transaction], int]:
        if holding_id:
            holding = await self.get_holding(holding_id, user_id)
            return await self.transaction_repo.list_by_holding(holding.id, limit, offset)
        if portfolio_id:
            await self.get_portfolio(portfolio_id, user_id)
            return await self.transaction_repo.list_by_portfolio(portfolio_id, limit, offset)
        raise ValueError("Either holding_id or portfolio_id is required")
