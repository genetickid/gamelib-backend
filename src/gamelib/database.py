from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from gamelib.config import settings

engine = create_async_engine(settings.async_database_url)

SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        yield session
