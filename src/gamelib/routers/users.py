from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from gamelib.constants import (
    USER_NOT_FOUND_MSG, GAME_NOT_FOUND_MSG, PG_UNIQUE_VIOLATION,
    PG_FK_VIOLATION
)
from gamelib.database import get_db
from gamelib.dependencies import get_current_user, require_role, require_staff_or_owner
from gamelib.exceptions.common import LibraryEntryAlreadyExistsError, ObjNotFoundError, UserAlreadyExistsError
from gamelib.exceptions.web import LastAdminProtectionError
from gamelib.models import User, Game, UserGame
from gamelib.schemas import (
    UserCreate, Username, UserRead, UserRole, UserUpdate, UserLibraryEntryRead, UserGameWrite, UserGameUpdate
)
from gamelib.utils.db import create_user_in_db, is_user_last_admin
from gamelib.utils.web import get_obj_or_404

router = APIRouter(
    prefix='/users',
    tags=['users'],
    dependencies=[Depends(get_current_user)]
)


@router.get('/me')
async def me(user: User = Depends(get_current_user)) -> UserRead:
    return user


@router.post(
    '', status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.ADMIN))]
)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    return await create_user_in_db(db, user_data, role=user_data.role)


@router.get(
    '/{user_id}',
    dependencies=[Depends(require_staff_or_owner)]
)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)) -> UserRead:
    return await get_obj_or_404(
        db_model=User,
        pk=user_id,
        db=db,
        error_msg=USER_NOT_FOUND_MSG
    )


@router.patch(
    '/{user_id}',
    dependencies=[Depends(require_staff_or_owner)]
)
async def update_user(
    user_id: int,
    update_data: UserUpdate,
    db: AsyncSession = Depends(get_db)
) -> UserRead:
    user = await get_obj_or_404(
        db_model=User,
        pk=user_id,
        db=db,
        error_msg=USER_NOT_FOUND_MSG
    )
    update_data_dict = update_data.model_dump(exclude_unset=True)
    if not update_data_dict:
        return user

    for field_name, new_value in update_data_dict.items():
        setattr(user, field_name, new_value)
    await db.commit()

    return user


@router.put(
    '/{user_id}/role',
    dependencies=[Depends(require_role(UserRole.ADMIN))]
)
async def update_role(
    user_id: int,
    role: UserRole = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
) -> UserRead:
    user = await get_obj_or_404(
        db_model=User,
        pk=user_id,
        db=db,
        error_msg=USER_NOT_FOUND_MSG
    )
    is_last_admin = await is_user_last_admin(db, user)
    if is_last_admin and role != UserRole.ADMIN:
        raise LastAdminProtectionError()
    user.role = role
    await db.commit()
    return user


@router.put(
    '/{user_id}/username',
    dependencies=[Depends(require_staff_or_owner)]
)
async def update_username(
    user_id: int,
    username: Username = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
) -> UserRead:
    user = await get_obj_or_404(
        db_model=User,
        pk=user_id,
        db=db,
        error_msg=USER_NOT_FOUND_MSG
    )
    user.username = username
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise UserAlreadyExistsError()

    return user


@router.delete(
    '/{user_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_staff_or_owner)]
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    user = await get_obj_or_404(
        db_model=User,
        pk=user_id,
        db=db,
        error_msg=USER_NOT_FOUND_MSG
    )
    is_last_admin = await is_user_last_admin(db, user)
    if is_last_admin:
        raise LastAdminProtectionError()

    await db.delete(user)
    await db.commit()


@router.post(
    '/{user_id}/library',
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_staff_or_owner)]
)
async def create_library_entry(
    user_id: int,
    library_entry: UserGameWrite,
    db: AsyncSession = Depends(get_db)
) -> UserLibraryEntryRead:
    game = await get_obj_or_404(
        db_model=Game,
        pk=library_entry.game_id,
        db=db,
        error_msg=GAME_NOT_FOUND_MSG
    )
    await get_obj_or_404(
        db_model=User,
        pk=user_id,
        db=db,
        error_msg=USER_NOT_FOUND_MSG
    )
    new_library_entry = UserGame(
        user_id=user_id,
        game=game,
        **library_entry.model_dump()
    )

    db.add(new_library_entry)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        error_code = exc.orig.sqlstate
        if error_code == PG_FK_VIOLATION:
            raise ObjNotFoundError(GAME_NOT_FOUND_MSG)
        elif error_code == PG_UNIQUE_VIOLATION:
            raise LibraryEntryAlreadyExistsError()
        else:
            raise
    
    await db.refresh(new_library_entry)
    return new_library_entry
