import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin


class TransactionType(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"
    BONUS = "BONUS"
    SPLIT = "SPLIT"


transaction_type_enum = ENUM(TransactionType, name="transaction_type", create_type=True)


class Transaction(Base, UUIDMixin):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_holding_id", "holding_id"),
        Index("ix_transactions_timestamp", "timestamp"),
    )

    holding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("holdings.id", ondelete="CASCADE"),
        nullable=False,
    )
    transaction_type: Mapped[TransactionType] = mapped_column(
        transaction_type_enum, nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    holding = relationship("Holding", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction {self.transaction_type.value} {self.quantity}>"
