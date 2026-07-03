"""Analytics service -- orchestrates all analytics computations for a portfolio."""

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics import allocation as alloc_mod
from app.analytics import risk as risk_mod
from app.analytics import tax as tax_mod
from app.analytics.cagr import cagr
from app.analytics.pnl import realized_pnl_from_sells, unrealized_pnl
from app.analytics.xirr import xirr
from app.exceptions import XIRRConvergenceError
from app.repositories.holding import HoldingRepository
from app.repositories.market_snapshot import MarketSnapshotRepository
from app.repositories.portfolio_snapshot import PortfolioSnapshotRepository
from app.repositories.transaction import TransactionRepository
from app.utils.decimal import safe_divide, to_str

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.holding_repo = HoldingRepository(db)
        self.transaction_repo = TransactionRepository(db)
        self.snapshot_repo = PortfolioSnapshotRepository(db)
        self.market_repo = MarketSnapshotRepository(db)

    async def get_performance(self, portfolio_id: UUID) -> dict:
        """Compute XIRR, CAGR, absolute returns, and P&L for a portfolio."""
        holdings = await self.holding_repo.list_by_portfolio(portfolio_id)
        if not holdings:
            return self._empty_performance()

        # Gather current prices and compute portfolio-level values
        total_current_value = Decimal("0")
        total_invested = Decimal("0")
        total_unrealized = Decimal("0")
        total_realized = Decimal("0")
        total_daily = Decimal("0")

        cash_flows: list[float] = []
        cash_flow_dates: list = []

        for holding in holdings:
            price_row = await self.market_repo.get_latest_by_symbol(holding.symbol)
            current_price = price_row.market_price if price_row else holding.average_buy_price

            holding_value = holding.quantity * current_price
            holding_invested = holding.quantity * holding.average_buy_price
            total_current_value += holding_value
            total_invested += holding_invested
            total_unrealized += unrealized_pnl(holding, current_price)

            # Realized P&L from sells
            sells = await self.transaction_repo.get_sells_for_holding(holding.id)
            total_realized += realized_pnl_from_sells(sells, holding.average_buy_price)

            # Build XIRR cash-flow series from all transactions
            txns = await self.transaction_repo.list_all_for_holding(holding.id)
            for txn in txns:
                from app.models.transaction import TransactionType

                if txn.transaction_type == TransactionType.BUY:
                    cash_flows.append(-float(txn.quantity * txn.price))
                    cash_flow_dates.append(txn.timestamp)
                elif txn.transaction_type in (
                    TransactionType.SELL,
                    TransactionType.DIVIDEND,
                ):
                    cash_flows.append(float(txn.quantity * txn.price))
                    cash_flow_dates.append(txn.timestamp)
                # BONUS/SPLIT don't generate cash flows, so skip them

        # Append current portfolio value as final synthetic cash flow
        from datetime import UTC, datetime

        now = datetime.now(UTC)
        if cash_flows:
            cash_flows.append(float(total_current_value))
            cash_flow_dates.append(now)

        # Time span in days
        from app.utils.dates import days_between

        days = 0
        if cash_flow_dates:
            days = days_between(cash_flow_dates[0], cash_flow_dates[-1])

        # XIRR
        xirr_value = None
        try:
            if len(cash_flows) >= 2 and days >= 1:
                xirr_value = xirr(cash_flows, cash_flow_dates)
        except XIRRConvergenceError:
            logger.warning("XIRR did not converge for portfolio %s", portfolio_id)

        # CAGR
        cagr_value = None
        if total_invested > 0 and days >= 1:
            cagr_value = cagr(total_invested, total_current_value, days)

        # Absolute return (always available)
        abs_return = safe_divide((total_current_value - total_invested) * 100, total_invested)

        return {
            "xirr": to_str(Decimal(str(round(xirr_value * 100, 2)))) if xirr_value else None,
            "cagr": to_str(cagr_value * 100) if cagr_value else None,
            "absolute_return_percent": to_str(abs_return),
            "unrealized_pnl": to_str(total_unrealized),
            "realized_pnl": to_str(total_realized),
            "daily_pnl": to_str(total_daily),
        }

    async def get_allocation(self, portfolio_id: UUID) -> dict:
        """Compute allocation breakdowns and diversification score."""
        holdings = await self.holding_repo.list_by_portfolio(portfolio_id)
        if not holdings:
            return self._empty_allocation()

        by_asset: dict[str, Decimal] = {}
        total_value = Decimal("0")
        largest_symbol = ""
        largest_value = Decimal("0")

        for holding in holdings:
            price_row = await self.market_repo.get_latest_by_symbol(holding.symbol)
            current_price = price_row.market_price if price_row else holding.average_buy_price
            value = holding.quantity * current_price
            total_value += value

            asset_key = holding.asset_type.value
            by_asset[asset_key] = by_asset.get(asset_key, Decimal("0")) + value

            if value > largest_value:
                largest_value = value
                largest_symbol = holding.symbol

        # Diversification score from holding weights
        weights = (
            [safe_divide(v, total_value) for v in by_asset.values()] if total_value > 0 else []
        )
        div_score = alloc_mod.diversification_score(weights)

        asset_alloc = alloc_mod.compute_allocation(by_asset, total_value)
        largest_pct = (
            safe_divide(largest_value * 100, total_value) if total_value > 0 else Decimal("0")
        )

        return {
            "by_asset_type": [
                {"asset_type": a["label"], "percent": a["percent"]} for a in asset_alloc
            ],
            "by_market_cap": [],  # requires external data enrichment
            "by_sector": [],  # requires external data enrichment
            "diversification_score": to_str(div_score),
            "largest_holding": {
                "symbol": largest_symbol,
                "percent": to_str(largest_pct, 1),
            }
            if largest_symbol
            else None,
        }

    async def get_risk(self, portfolio_id: UUID) -> dict:
        """Compute risk metrics from portfolio snapshot history."""
        snapshots = await self.snapshot_repo.list_by_portfolio(portfolio_id, limit=60)
        snapshots = list(reversed(snapshots))  # oldest first

        # Daily returns from snapshot values
        daily_returns = []
        for i in range(1, len(snapshots)):
            prev_val = float(snapshots[i - 1].portfolio_value)
            curr_val = float(snapshots[i].portfolio_value)
            if prev_val > 0:
                daily_returns.append((curr_val - prev_val) / prev_val)

        vol = risk_mod.volatility_from_returns(daily_returns)

        # Concentration from holdings
        holdings = await self.holding_repo.list_by_portfolio(portfolio_id)
        total = Decimal("0")
        max_val = Decimal("0")
        for h in holdings:
            price_row = await self.market_repo.get_latest_by_symbol(h.symbol)
            price = price_row.market_price if price_row else h.average_buy_price
            val = h.quantity * price
            total += val
            if val > max_val:
                max_val = val

        largest_weight = float(safe_divide(max_val, total)) if total > 0 else 0.0
        conc = risk_mod.concentration_risk(largest_weight)

        return {
            "volatility_30d": str(round(vol, 4)) if vol is not None else None,
            "concentration_risk": conc,
            "beta_vs_nifty50": None,  # requires benchmark data
        }

    async def get_tax(self, portfolio_id: UUID) -> dict:
        """Compute dividend income and tax-loss harvesting candidates."""
        holdings = await self.holding_repo.list_by_portfolio(portfolio_id)
        total_dividends = Decimal("0")
        holdings_with_prices = []

        for holding in holdings:
            # Dividend income
            divs = await self.transaction_repo.get_dividends_for_holding(holding.id)
            total_dividends += tax_mod.sum_dividend_income(divs)

            # Current price for loss harvesting
            price_row = await self.market_repo.get_latest_by_symbol(holding.symbol)
            current_price = price_row.market_price if price_row else holding.average_buy_price

            if holding.quantity > 0:
                holdings_with_prices.append(
                    {
                        "holding_id": str(holding.id),
                        "symbol": holding.symbol,
                        "quantity": holding.quantity,
                        "average_buy_price": holding.average_buy_price,
                        "current_price": current_price,
                    }
                )

        candidates = tax_mod.find_tax_loss_candidates(holdings_with_prices)

        return {
            "dividend_income": to_str(total_dividends),
            "tax_loss_opportunities": candidates,
        }

    def _empty_performance(self) -> dict:
        return {
            "xirr": None,
            "cagr": None,
            "absolute_return_percent": "0.00",
            "unrealized_pnl": "0.00",
            "realized_pnl": "0.00",
            "daily_pnl": "0.00",
        }

    def _empty_allocation(self) -> dict:
        return {
            "by_asset_type": [],
            "by_market_cap": [],
            "by_sector": [],
            "diversification_score": "0.00",
            "largest_holding": None,
        }
