from typing import Callable
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from gamelib.config import settings
from gamelib.database import get_db
from gamelib.models import UserModel
from gamelib.schemas import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/login')

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserModel:
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

    user = db.get(UserModel, user_id)

    if user is None:
        raise credentials_exception

    return user


def require_role(*roles: UserRole) -> Callable[[UserModel], UserModel]:
    def check_role(user: UserModel = Depends(get_current_user)) -> UserModel:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You have no rights to do this!!'
            )
        return user
    return check_role


def require_staff_or_owner(
    user_id: int, current_user: UserModel = Depends(get_current_user)
) -> None:
    if not current_user.is_staff and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )
