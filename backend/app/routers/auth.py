from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import create_token, get_current_user, hash_password, verify_password
from ..db import get_session
from ..models import User
from ..ratelimit import limit_auth
from ..schemas import LoginIn, RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201, dependencies=[Depends(limit_auth)])
async def register(data: RegisterIn, session: AsyncSession = Depends(get_session)):
    email = data.email.lower().strip()
    existing = await session.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Bu email artıq qeydiyyatdadır")
    user = User(email=email, password_hash=hash_password(data.password))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return TokenOut(token=create_token(user.id), email=user.email)


@router.post("/login", response_model=TokenOut, dependencies=[Depends(limit_auth)])
async def login(data: LoginIn, session: AsyncSession = Depends(get_session)):
    email = data.email.lower().strip()
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email və ya parol yanlışdır")
    return TokenOut(token=create_token(user.id), email=user.email)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user
