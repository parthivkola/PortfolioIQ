from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import AuthService
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.core.redis import get_redis
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    svc = AuthService(db, redis)
    return await svc.register(body.email, body.password, body.full_name)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    svc = AuthService(db, redis)
    return await svc.login(body.email, body.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    svc = AuthService(db, redis)
    return await svc.refresh(body.refresh_token)


@router.post("/logout", status_code=204)
async def logout(
    user_id=Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    svc = AuthService(db, redis)
    await svc.logout(str(user_id))
