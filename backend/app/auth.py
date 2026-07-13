"""Sadə JWT auth: bcrypt hash + HS256 token. SSE üçün token query param ilə də qəbul olunur."""

import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .db import get_session
from .models import User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_token(user_id: uuid.UUID) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.jwt_expire_days),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


async def get_current_user(
    request: Request,
    token: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> User:
    # EventSource header qoya bilmir — Bearer header yoxdursa ?token= qəbul edilir
    auth_header = request.headers.get("Authorization", "")
    raw = auth_header.removeprefix("Bearer ").strip() if auth_header.startswith("Bearer ") else token
    if not raw:
        raise HTTPException(status_code=401, detail="Token tələb olunur")
    try:
        payload = jwt.decode(raw, settings.jwt_secret, algorithms=["HS256"])
        user_id = uuid.UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Token etibarsızdır")
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="İstifadəçi tapılmadı")
    return user
