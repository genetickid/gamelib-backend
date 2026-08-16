from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from gamelib.exceptions.common import UserAlreadyExistsError
from gamelib.models import User
from gamelib.schemas import UserAuth, UserRole
from gamelib.security import get_password_hash


async def create_user_in_db(
    db: AsyncSession,
    user_data: UserAuth,
    role: UserRole
) -> User:
    password_hash = get_password_hash(user_data.password)
    fields_to_include = set(UserAuth.model_fields.keys())
    fields_to_exclude = {'password'}
    user_data_dict = user_data.model_dump(
        include=fields_to_include,
        exclude=fields_to_exclude
    )
    user = User(
        password_hash=password_hash,
        role=role,
        **user_data_dict
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise UserAlreadyExistsError()

    return user

async def is_user_last_admin(db: AsyncSession, user: User) -> bool:
    if user.role != UserRole.ADMIN:
        return False

    stmt = (
        select(User.id)
        .where(User.role == UserRole.ADMIN)
        .with_for_update()
    )
    result = await db.scalars(stmt)
    admin_ids = result.all()

    return len(admin_ids) == 1
