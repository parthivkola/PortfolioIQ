import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class PortfolioSnapshot(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "portfoliosnapshot"
    __table_args__ = (
        Index("ix_portfoliosnapshot_portfolio_created", "portfolio_id", "created_at"),
    )

    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolio.id", ondelete="CASCADE"),
        nullable=False,
    )
    portfolio_value: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    invested_value: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    pnl: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)

    portfolio = relationship("Portfolio", back_populates="snapshots")

    def __repr__(self) -> str:
        return f"<PortfolioSnapshot value={self.portfolio_value}>"
