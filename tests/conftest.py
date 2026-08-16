import itertools

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from gamelib.config import settings
from gamelib.database import get_db
from gamelib.main import app
from gamelib.models import Base, User
from gamelib.schemas import UserRole
from gamelib.security import create_access_token


@pytest.fixture(scope='session')
async def engine():
    test_settings = settings.model_copy(update={'DB_NAME': 'gamelib_test'})
    engine = create_async_engine(test_settings.async_database_url)
    yield engine
    await engine.dispose()


@pytest.fixture(scope='session', autouse=True)
async def create_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope='function')
async def session(engine):
    connection = await engine.connect()
    transaction = await connection.begin()
    db_session = AsyncSession(
        bind=connection,
        join_transaction_mode='create_savepoint',
        expire_on_commit=False
    )
    yield db_session
    await db_session.close()
    await transaction.rollback()
    await connection.close()


@pytest.fixture(scope='function')
async def client(session):
    async def get_test_db():
        yield session

    app.dependency_overrides[get_db] = get_test_db
    yield AsyncClient(transport=ASGITransport(app), base_url='http://test')
    app.dependency_overrides.clear()


@pytest.fixture(scope='function')
def make_user(session):
    user_counter = itertools.count(start=1)
    async def factory(role: UserRole):
        user = User(
            username=f'test_user_{next(user_counter)}',
            role=role,
            password_hash='aboba123'
        )
        session.add(user)
        await session.flush()
        token = create_access_token(user.id)
        headers = {'Authorization': f'Bearer {token}'}
        return user.id, headers
    return factory
