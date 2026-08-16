from typing import Awaitable, Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from gamelib.config import settings
from gamelib.constants import USER_NOT_FOUND_MSG
from gamelib.database import get_db
from gamelib.exceptions.common import ObjNotFoundError
from gamelib.models import User
from gamelib.schemas import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/login')

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'}
    )
    try:
        payload = jwt.decode(
            jwt=token,
            key=settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = int(payload.get('sub'))
    except (InvalidTokenError, TypeError, ValueError):
        raise credentials_exception

    user = await db.get(User, user_id)

    if user is None:
        raise credentials_exception

    return user


def require_role(*roles: UserRole) -> Callable[[User], Awaitable[User]]:
    async def check_role(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You have no rights to do this!!'
            )
        return user
    return check_role


async def require_staff_or_owner(
    user_id: int, current_user: User = Depends(get_current_user)
) -> None:
    if not current_user.is_staff and current_user.id != user_id:
        raise ObjNotFoundError(USER_NOT_FOUND_MSG)
