"""Database storage service."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from epg_web.models.db import Base

# SQLite database URL (using aiosqlite for async support)
DATABASE_URL = "sqlite+aiosqlite:///epg.db"

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db():
    """Initialize the database with tables."""
    async with engine.begin() as conn:
        # Ensure old tables are removed so schema changes (like removed unique
        # constraints) are applied. In production you'd use migrations; for this
        # simple script we drop and recreate.
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()