from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gamelib.database import get_db
from gamelib.models import User
from gamelib.schemas import Token, UserAuth, UserRead, UserRole
from gamelib.security import (
    DUMMY_HASH,
    create_access_token,
    verify_password,
)
from gamelib.utils.db import create_user_in_db

router = APIRouter(prefix='/auth', tags=['auth'])

@router.post('/register', status_code=status.HTTP_201_CREATED)
async def register(user_data: UserAuth, db: AsyncSession = Depends(get_db)) -> UserRead:
    return await create_user_in_db(db, user_data, role=UserRole.USER)

@router.post('/login')
async def login(
    user_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Token:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Incorrect username or password',
        headers={'WWW-Authenticate': 'Bearer'}
    )
    stmt = select(User).where(User.username == user_data.username)
    user = await db.scalar(stmt)
    if user is None:
        verify_password(user_data.password, DUMMY_HASH)
        raise credentials_exception

    if not verify_password(user_data.password, user.password_hash):
        raise credentials_exception

    access_token = create_access_token(user.id)
    return Token(access_token=access_token, token_type='bearer')
