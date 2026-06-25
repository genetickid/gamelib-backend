from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from gamelib.database import get_db
from gamelib.models import UserModel
from gamelib.schemas import Token, UserAuth, UserRead, UserRole
from gamelib.security import (
    DUMMY_HASH,
    create_access_token,
    verify_password,
)
from gamelib.utils.db import create_user_in_db

router = APIRouter(prefix='/auth', tags=['auth'])

@router.post('/register', status_code=status.HTTP_201_CREATED)
def register(user_data: UserAuth, db: Session = Depends(get_db)) -> UserRead:
    return create_user_in_db(db, user_data, role=UserRole.USER)

@router.post('/login')
def login(
    user_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Token:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Incorrect username or password',
        headers={'WWW-Authenticate': 'Bearer'}
    )
    stmt = select(UserModel).where(UserModel.username == user_data.username)
    user = db.scalar(stmt)
    if user is None:
        verify_password(user_data.password, DUMMY_HASH)
        raise credentials_exception

    if not verify_password(user_data.password, user.password_hash):
        raise credentials_exception

    access_token = create_access_token(user.id)
    return Token(access_token=access_token, token_type='bearer')
