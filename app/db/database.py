import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///./wakeonlan.db")

engine = create_async_engine(DB_URL, echo=False, future=True)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = DeclarativeBase()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Async database session dependency.

    Yields a session, commits on success, rolls back on exception, closes at end.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
