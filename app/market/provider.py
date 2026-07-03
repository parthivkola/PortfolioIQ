"""Market data provider abstraction with Yahoo Finance implementation."""

import abc
import logging
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class MarketDataProvider(abc.ABC):
    """Interface for market data sources. Swap implementations without touching callers."""

    @abc.abstractmethod
    async def get_quote(self, symbol: str) -> dict | None:
        """Return {"price": Decimal, "as_of": datetime} or None on failure."""

    @abc.abstractmethod
    async def search(self, query: str) -> list[dict]:
        """Return list of {"symbol", "name", "asset_type"} matches."""

    @abc.abstractmethod
    async def get_history(self, symbol: str, period: str) -> list[dict]:
        """Return list of {"date": str, "close": str} daily points."""


class YahooFinanceProvider(MarketDataProvider):
    """Yahoo Finance adapter using the yfinance library.

    All calls are run in a thread executor because yfinance is synchronous.
    """

    async def get_quote(self, symbol: str) -> dict | None:
        import asyncio

        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, self._sync_quote, symbol)
        except Exception:
            logger.exception("yahoo finance quote failed for %s", symbol)
            return None

    async def search(self, query: str) -> list[dict]:
        import asyncio

        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, self._sync_search, query)
        except Exception:
            logger.exception("yahoo finance search failed for %s", query)
            return []

    async def get_history(self, symbol: str, period: str) -> list[dict]:
        import asyncio

        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, self._sync_history, symbol, period)
        except Exception:
            logger.exception("yahoo finance history failed for %s", symbol)
            return []

    def _sync_quote(self, symbol: str) -> dict | None:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        price = getattr(info, "last_price", None)
        if price is None:
            return None
        return {
            "price": Decimal(str(round(price, 4))),
            "as_of": datetime.now().isoformat(),
        }

    def _sync_search(self, query: str) -> list[dict]:
        import yfinance as yf

        results = yf.Search(query)
        output = []
        for item in getattr(results, "quotes", [])[:10]:
            output.append(
                {
                    "symbol": item.get("symbol", ""),
                    "name": item.get("shortname", item.get("longname", "")),
                    "asset_type": item.get("quoteType", "STOCK"),
                }
            )
        return output

    def _sync_history(self, symbol: str, period: str) -> list[dict]:
        import yfinance as yf

        period_map = {"1M": "1mo", "3M": "3mo", "1Y": "1y", "5Y": "5y"}
        yf_period = period_map.get(period, "1mo")

        ticker = yf.Ticker(symbol)
        df = ticker.history(period=yf_period)
        points = []
        for idx, row in df.iterrows():
            points.append(
                {
                    "date": idx.strftime("%Y-%m-%d"),
                    "close": str(round(row["Close"], 4)),
                }
            )
        return points
