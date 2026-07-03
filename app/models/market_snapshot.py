from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class MarketSnapshot(Base, UUIDMixin):
    __tablename__ = "marketsnapshot"
    __table_args__ = (UniqueConstraint("symbol", "timestamp", name="ux_marketsnapshot_symbol_ts"),)

    symbol: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    market_price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return f"<MarketSnapshot {self.symbol} @ {self.market_price}>"
