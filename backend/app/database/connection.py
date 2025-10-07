"""
Database connection utilities for both sync and async operations.

This module provides database session management for the application.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import create_engine

from utils.settings import get_settings


# Sync database setup
def get_engine():
    """Get synchronous database engine."""
    database_url = get_settings().DATABASE_CONNECTION_STRING
    return create_engine(database_url, echo=False)


# Async database setup
def get_async_engine():
    """Get asynchronous database engine."""
    database_url = get_settings().DATABASE_CONNECTION_STRING
    # Convert postgresql:// to postgresql+asyncpg:// for async operations
    if database_url.startswith("postgresql://"):
        async_database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        async_database_url = database_url

    return create_async_engine(async_database_url, echo=False)


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get an async database session.

    Yields:
        AsyncSession: The async database session
    """
    async_engine = get_async_engine()
    async with AsyncSession(async_engine) as session:
        try:
            yield session
        finally:
            await session.close()
