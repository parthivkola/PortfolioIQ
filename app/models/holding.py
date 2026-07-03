import enum
import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin


class AssetType(str, enum.Enum):
    STOCK = "STOCK"
    ETF = "ETF"
    MUTUAL_FUND = "MUTUAL_FUND"
    CRYPTO = "CRYPTO"
    BOND = "BOND"


asset_type_enum = ENUM(AssetType, name="asset_type", create_type=True)


class Holding(Base, UUIDMixin):
    __tablename__ = "holdings"
    __table_args__ = (
        UniqueConstraint("portfolio_id", "symbol", name="ux_holdings_portfolio_symbol"),
    )

    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolio.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_type: Mapped[AssetType] = mapped_column(asset_type_enum, nullable=False)
    symbol: Mapped[str] = mapped_column(String(40), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False, default=Decimal("0"))
    average_buy_price: Mapped[Decimal] = mapped_column(
        Numeric(20, 4), nullable=False, default=Decimal("0")
    )

    portfolio = relationship("Portfolio", back_populates="holdings")
    transactions = relationship(
        "Transaction", back_populates="holding", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Holding {self.symbol} qty={self.quantity}>"
