"""
Database connection utilities for both sync and async operations.

This module provides database session management for the application.
"""

import re
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import create_engine

from utils.settings import get_settings


# Sync database setup
def get_engine():
    """Get synchronous database engine."""
    database_url = get_settings().DATABASE_CONNECTION_STRING
    # Handle SSL mode for psycopg2 - ensure valid sslmode values
    if "sslmode=" in database_url:
        # Find all sslmode parameters and their values
        sslmode_matches = re.findall(r"sslmode=([^&]*)", database_url)

        if sslmode_matches:
            # Use the last sslmode value found (most specific)
            sslmode_value = sslmode_matches[-1].strip().lower()  # Case-insensitive

            # Validate and normalize sslmode value for psycopg2
            valid_sslmodes = ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]

            # Normalize common invalid values (case-insensitive)
            sslmode_mapping = {
                "true": "require",
                "false": "disable",
                "1": "require",
                "0": "disable",
                "yes": "require",
                "no": "disable",
                "on": "require",
                "off": "disable"
            }

            if sslmode_value in sslmode_mapping:
                sslmode_value = sslmode_mapping[sslmode_value]
            elif sslmode_value not in valid_sslmodes:
                # Default to require for unknown invalid values
                sslmode_value = "require"

            # Remove all existing sslmode parameters first, then add the correct one
            database_url = re.sub(r"[?&]sslmode=[^&]*", "", database_url)
            # Add the correct sslmode parameter
            separator = "&" if "?" in database_url else "?"
            database_url = f"{database_url}{separator}sslmode={sslmode_value}"

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

    # Handle SSL mode for asyncpg - convert sslmode to ssl parameter
    if "sslmode=" in async_database_url:
        import re
        # Find all sslmode parameters and their values
        sslmode_matches = re.findall(r"sslmode=([^&]*)", async_database_url)

        if sslmode_matches:
            # Use the last sslmode value found (most specific)
            sslmode_value = sslmode_matches[-1].strip().lower()  # Case-insensitive

            # Convert sslmode to ssl parameter for asyncpg
            if sslmode_value in ["require", "prefer", "allow"]:
                ssl_value = "true"
            elif sslmode_value == "disable":
                ssl_value = "false"
            elif sslmode_value == "":
                # Handle sslmode= without value - default to secure
                ssl_value = "true"
            else:
                ssl_value = "true"  # Default to secure for unknown values

            # Remove all existing sslmode parameters first, then add ssl parameter
            async_database_url = re.sub(r"[?&]sslmode=[^&]*", "", async_database_url)
            # Add the ssl parameter
            separator = "&" if "?" in async_database_url else "?"
            async_database_url = f"{async_database_url}{separator}ssl={ssl_value}"

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
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
