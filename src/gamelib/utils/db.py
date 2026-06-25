from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from gamelib.models import UserModel
from gamelib.schemas import UserAuth, UserRole
from gamelib.security import get_password_hash
from gamelib.exceptions import UserAlreadyExistsError

def create_user_in_db(
    db: Session,
    user_data: UserAuth,
    role: UserRole
) -> UserModel:
    password_hash = get_password_hash(user_data.password)
    fields_to_include = set(UserAuth.model_fields.keys())
    fields_to_exclude = {'password'}
    user_data_dict = user_data.model_dump(
        include=fields_to_include,
        exclude=fields_to_exclude
    )
    user = UserModel(
        password_hash=password_hash,
        role=role,
        **user_data_dict
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise UserAlreadyExistsError('User with this username already exists')

    return user
