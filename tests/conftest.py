import itertools
from contextlib import contextmanager

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from gamelib.config import settings
from gamelib.database import get_db
from gamelib.main import app
from gamelib.models import Base, Game, User
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
        async with AsyncSession(
            bind=session.bind,
            join_transaction_mode='create_savepoint',
            expire_on_commit=False
        ) as http_request_session:
            yield http_request_session

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


@pytest.fixture(scope='function')
def make_game(session):
    game_counter = itertools.count(start=1)
    async def factory():
        game = Game(
           title=f'test_game_{next(game_counter)}',
           genre='shooter',
           release_date=None
        )
        session.add(game)
        await session.flush()
        return game
    return factory


@pytest.fixture(scope='function')
def query_counter(engine):
    TRACKED_COMMANDS = {'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH'}

    @contextmanager
    def counter():
        queries = []

        def before_cursor_execute(conn, cursor, statement, *args):
            parts = statement.strip().split(maxsplit=1)
            if parts and parts[0].upper() in TRACKED_COMMANDS:
                queries.append(statement)

        event.listen(engine.sync_engine, 'before_cursor_execute', before_cursor_execute)
        try:
            yield queries
        finally:
            event.remove(engine.sync_engine, 'before_cursor_execute', before_cursor_execute)

    return counter

