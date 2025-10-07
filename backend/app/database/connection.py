"""
Database connection utilities for both sync and async operations.

This module provides database session management for the application.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import create_engine

from utils.settings import get_settings


def _normalize_ssl_mode(database_url: str, for_async: bool = False) -> str:
    """
    Normalize SSL mode parameters in database connection string.

    Args:
        database_url: The database connection string
        for_async: If True, convert sslmode to ssl for asyncpg compatibility

    Returns:
        str: Normalized database connection string
    """
    try:
        # Parse the URL
        parsed = urlparse(database_url)
        query_params = parse_qs(parsed.query)

        # Check if sslmode exists
        if "sslmode" not in query_params:
            return database_url

        # Get the last sslmode value (most specific)
        sslmode_value = query_params["sslmode"][-1].strip().lower()

        if for_async:
            # Convert sslmode to ssl for asyncpg
            if sslmode_value in ["require", "prefer", "allow"]:
                ssl_value = "true"
            elif sslmode_value == "disable":
                ssl_value = "false"
            elif sslmode_value == "":
                ssl_value = "true"  # Default to secure
            else:
                ssl_value = "true"  # Default to secure for unknown values

            # Remove sslmode and add ssl
            del query_params["sslmode"]
            query_params["ssl"] = [ssl_value]
        else:
            # Normalize sslmode for psycopg2
            valid_sslmodes = ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]

            # Normalize common invalid values
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
                sslmode_value = "require"  # Default to secure

            # Update sslmode value
            query_params["sslmode"] = [sslmode_value]

        # Rebuild the URL
        new_query = urlencode(query_params, doseq=True)
        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)

    except Exception:
        # If URL parsing fails, return original URL
        return database_url


# Sync database setup
def get_engine():
    """Get synchronous database engine."""
    database_url = get_settings().DATABASE_CONNECTION_STRING
    # Normalize SSL mode for psycopg2
    database_url = _normalize_ssl_mode(database_url, for_async=False)
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

    # Normalize SSL mode for asyncpg (convert sslmode to ssl)
    async_database_url = _normalize_ssl_mode(async_database_url, for_async=True)
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
