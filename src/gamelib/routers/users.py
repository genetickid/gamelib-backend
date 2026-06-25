from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from gamelib.database import get_db
from gamelib.dependencies import (
    get_current_user, require_role, require_staff_or_owner
)
from gamelib.models import UserModel
from gamelib.schemas import UserCreate, UserRead, UserRole
from gamelib.utils.db import create_user_in_db

router = APIRouter(
    prefix='/users',
    tags=['users'],
    dependencies=[Depends(get_current_user)]
)


@router.get('/me')
def me(user: UserModel = Depends(get_current_user)) -> UserRead:
    return user


@router.get(
    '/{user_id}',
    dependencies=[Depends(require_staff_or_owner)]
)
def get_user(user_id: int, db: Session = Depends(get_db)) -> UserRead:
    user = db.get(UserModel, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )
    return user


@router.post(
    '', status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.ADMIN))]
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
) -> UserRead:
    return create_user_in_db(db, user_data, role=user_data.role)
