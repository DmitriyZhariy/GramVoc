from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.config import settings


# sync_maker = sessionmaker() # TODO : find out am I need this
engine = create_async_engine(
    "postgresql+asyncpg://USER:PASSWORD@db/DB_NAME", echo=False)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    # sync_session_class=sync_maker,
)

class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session_factory() as session:
        yield session