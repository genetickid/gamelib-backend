from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from gamelib.config import settings

password_hash = PasswordHash((Argon2Hasher(),))

DUMMY_HASH = password_hash.hash(settings.DUMMY_PASS)


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(user_id: int) -> str:
    exp = (
        datetime.now(timezone.utc)
        + timedelta(minutes=settings.ACCESS_TOKEN_EXP_MINS)
    )
    payload = {
        "sub": str(user_id),
        "exp": exp
    }
    access_token = jwt.encode(
        payload=payload,
        key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return access_token
