from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from src.config import settings


engine = create_async_engine(
    settings.DB_URL, echo=False)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    """
    Parent class for tables in db.
    """
    pass


async def get_db():
    """
    Provide an asynchronous db session..

    Yields:
        AsyncSession: A new session to work with a db.
    """
    async with async_session_factory() as session:
        yield session