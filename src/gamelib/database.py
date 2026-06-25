from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from gamelib.config import settings

connect_args = {'check_same_thread': False}

engine = create_engine(settings.DB_URL, connect_args=connect_args)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db():
    with SessionLocal() as session:
        yield session
