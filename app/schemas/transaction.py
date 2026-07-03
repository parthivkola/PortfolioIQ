from datetime import datetime

from pydantic import BaseModel, Field

from app.models.transaction import TransactionType


class TransactionCreate(BaseModel):
    holding_id: str
    transaction_type: TransactionType
    quantity: str = Field(..., description="Units transacted, as a decimal string")
    price: str = Field(..., description="Price per unit, as a decimal string")
    timestamp: datetime


class TransactionResponse(BaseModel):
    id: str
    holding_id: str
    transaction_type: TransactionType
    quantity: str
    price: str
    timestamp: datetime

    model_config = {"from_attributes": True}
