from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.portfolio.service import PortfolioService
from app.schemas.common import PaginationMeta
from app.schemas.transaction import TransactionCreate, TransactionResponse

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("")
async def list_transactions(
    holding_id: UUID | None = Query(None),
    portfolio_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = PortfolioService(db)
    offset = (page - 1) * limit
    txns, total = await svc.list_transactions(
        user_id, holding_id=holding_id, portfolio_id=portfolio_id, limit=limit, offset=offset
    )
    return {
        "data": [
            TransactionResponse(
                id=str(t.id),
                holding_id=str(t.holding_id),
                transaction_type=t.transaction_type,
                quantity=str(t.quantity),
                price=str(t.price),
                timestamp=t.timestamp,
            )
            for t in txns
        ],
        "meta": PaginationMeta(page=page, limit=limit, total=total),
    }


@router.post("", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    body: TransactionCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = PortfolioService(db)
    txn = await svc.process_transaction(
        holding_id=UUID(body.holding_id),
        user_id=user_id,
        transaction_type=body.transaction_type,
        quantity=Decimal(body.quantity),
        price=Decimal(body.price),
        timestamp=body.timestamp,
    )
    return TransactionResponse(
        id=str(txn.id),
        holding_id=str(txn.holding_id),
        transaction_type=txn.transaction_type,
        quantity=str(txn.quantity),
        price=str(txn.price),
        timestamp=txn.timestamp,
    )
