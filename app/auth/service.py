import logging

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.exceptions import AuthError
from app.repositories.user import UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession, redis: aioredis.Redis):
        self.repo = UserRepository(db)
        self.redis = redis

    async def register(self, email: str, password: str, full_name: str) -> dict:
        existing = await self.repo.get_by_email(email)
        if existing:
            raise AuthError("Email already registered", code="AUTH_001")

        hashed = hash_password(password)
        user = await self.repo.create(email=email, password_hash=hashed, full_name=full_name)
        logger.info("user registered: %s", user.id)

        access = create_access_token(str(user.id))
        refresh = create_refresh_token(str(user.id))
        await self._store_refresh(str(user.id), refresh)

        return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

    async def login(self, email: str, password: str) -> dict:
        user = await self.repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AuthError("Invalid email or password", code="AUTH_001")

        access = create_access_token(str(user.id))
        refresh = create_refresh_token(str(user.id))
        await self._store_refresh(str(user.id), refresh)
        logger.info("user logged in: %s", user.id)

        return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

    async def refresh(self, refresh_token: str) -> dict:
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise AuthError("Invalid refresh token", code="AUTH_003") from None

        if payload.get("type") != "refresh":
            raise AuthError("Invalid token type", code="AUTH_003")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthError("Invalid token payload", code="AUTH_003")

        # Check if this refresh token is still valid in Redis
        stored = await self.redis.get(f"refresh:{user_id}")
        if stored != refresh_token:
            # Possible token reuse -- invalidate the session entirely
            await self.redis.delete(f"refresh:{user_id}")
            logger.warning("refresh token reuse detected for user %s", user_id)
            raise AuthError("Refresh token reused, session invalidated", code="AUTH_003")

        # Rotate: issue new pair and store the new refresh token
        access = create_access_token(user_id)
        new_refresh = create_refresh_token(user_id)
        await self._store_refresh(user_id, new_refresh)

        return {"access_token": access, "refresh_token": new_refresh, "token_type": "bearer"}

    async def logout(self, user_id: str) -> None:
        await self.redis.delete(f"refresh:{user_id}")
        logger.info("user logged out: %s", user_id)

    async def _store_refresh(self, user_id: str, token: str) -> None:
        from app.core.config import settings

        ttl = settings.refresh_token_expire_days * 86400
        await self.redis.set(f"refresh:{user_id}", token, ex=ttl)
