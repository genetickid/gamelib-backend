from gamelib.database import SessionLocal
from gamelib.exceptions.common import UserAlreadyExistsError
from gamelib.schemas import UserAuth, UserRole
from gamelib.utils.db import create_user_in_db


def main():
    username = input('Username: ')
    password = input('Password: ')
    with SessionLocal() as db:
        try:
            user_auth_schema = UserAuth(
                username=username,
                password=password
            )
            create_user_in_db(db, user_auth_schema, UserRole.ADMIN)
            print('Superuser created.')
        except UserAlreadyExistsError:
            print('This username is already taken.')

if __name__ == '__main__':
    main()
