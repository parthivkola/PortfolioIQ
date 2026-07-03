from uuid import UUID

from fastapi import Depends, Header
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.exceptions import AuthError
from app.repositories.user import UserRepository


async def get_current_user_id(authorization: str = Header(...)) -> UUID:
    """Extract and validate user ID from the Authorization header."""
    if not authorization.startswith("Bearer "):
        raise AuthError("Invalid authorization header", code="AUTH_002")

    token = authorization.removeprefix("Bearer ")
    try:
        payload = decode_token(token)
    except JWTError:
        raise AuthError("Invalid or expired token", code="AUTH_002") from None

    if payload.get("type") != "access":
        raise AuthError("Invalid token type", code="AUTH_002")

    subject = payload.get("sub")
    if not subject:
        raise AuthError("Invalid token payload", code="AUTH_002")

    return UUID(subject)


async def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Load the full user object for the authenticated request."""
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise AuthError("User not found", code="AUTH_002")
    return user
