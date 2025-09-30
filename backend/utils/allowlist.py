"""Allowlist management with user-specific caching."""

import asyncio
import logging
import os
import time
from io import StringIO
from pathlib import Path

import aiofiles
import pandas as pd
from azure.storage.blob.aio import BlobServiceClient as AsyncBlobServiceClient

logger = logging.getLogger(__name__)


class UserAllowlistCache:
    """Thread-safe cache for individual user allowlist status with TTL.

    This class caches allowlist status per user rather than the entire
    allowlist table, reducing memory usage and improving performance.

    Attributes
    ----------
    _lock : asyncio.Lock
        Lock for thread-safe access to cache data.
    _user_status : Dict[str, bool]
        Cache of user email -> allowlist status.
    _expires_at : float
        Unix timestamp when the cache expires.
    _allowlist_data : Optional[pd.DataFrame]
        Cached allowlist DataFrame.
    """

    def __init__(self, ttl_seconds: int = 300) -> None:
        """Initialize the user allowlist cache.

        Parameters
        ----------
        ttl_seconds : int
            Time-to-live for cache entries in seconds.
        """
        self._lock = asyncio.Lock()
        self._user_status: dict[str, bool] = {}
        self._expires_at: float = 0.0
        self._allowlist_data: pd.DataFrame | None = None
        self._ttl_seconds = ttl_seconds

    def _is_valid(self) -> bool:
        """Check if the current cache is valid and not expired."""
        return (self._allowlist_data is not None) and (time.time() < self._expires_at)

    async def _load_allowlist_data(
        self,
        connection_string: str,
        container: str,
        blob_name: str,
        max_retries: int = 3
    ) -> pd.DataFrame:
        """Load allowlist data from Azure Blob Storage with retry logic.

        Falls back to local file in development if Azure fails.

        Parameters
        ----------
        connection_string : str
            Azure Storage connection string.
        container : str
            Blob container name.
        blob_name : str
            Blob name within the container.
        max_retries : int, default=3
            Maximum number of retry attempts.

        Returns
        -------
        pd.DataFrame
            DataFrame with Provider and Email columns.

        Raises
        ------
        Exception
            If Azure Blob Storage access fails after all retries and no local fallback.
        """
        last_exception = None
        for attempt in range(max_retries):
            try:
                # Create a new client for each attempt
                blob_service_client = AsyncBlobServiceClient.from_connection_string(
                    connection_string
                )

                async with blob_service_client:
                    blob_client = blob_service_client.get_blob_client(
                        container=container, blob=blob_name
                    )
                    stream = await blob_client.download_blob()
                    content: bytes = await stream.readall()

                    # Parse and validate inside the context manager
                    text = content.decode("utf-8")
                    allowlist_df = self._parse_allowlist_csv(text)

                    # Validate data quality
                    if not self._validate_allowlist_data(allowlist_df):
                        error_msg = "Allowlist data failed validation checks"
                        raise ValueError(error_msg)

                    logger.info("Successfully loaded allowlist from Azure: %s", blob_name)
                    return allowlist_df

            except Exception as e:
                last_exception = e
                logger.warning("Attempt %d/%d failed: %s", attempt + 1, max_retries, e)
                if attempt < max_retries - 1:  # Not the last attempt
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        # All Azure attempts failed - try local fallback in development
        if os.getenv("ENVIRONMENT", "").lower() == "local":
            logger.warning("Azure blob not found. Attempting local file fallback for development...")
            try:
                local_file = self._get_local_fallback_path(blob_name)
                if Path(local_file).exists():
                    # Use aiofiles for async file operations
                    async with aiofiles.open(local_file, encoding="utf-8") as f:
                        text = await f.read()
                    allowlist_df = self._parse_allowlist_csv(text)
                    if self._validate_allowlist_data(allowlist_df):
                        logger.info("✅ Using local fallback file: %s", local_file)
                        return allowlist_df
                else:
                    logger.error("Local fallback file not found: %s", local_file)
            except Exception:
                logger.exception("Local fallback also failed")

        # If we get here, all retries failed
        raise last_exception

    def _get_local_fallback_path(self, blob_name: str) -> str:
        """Get local file path for development fallback.

        Parameters
        ----------
        blob_name : str
            The Azure blob name (e.g., 'lookups/allowlist_dev.csv')

        Returns
        -------
        str
            Local file path
        """
        # Extract filename from blob path
        filename = Path(blob_name).name

        # Look in the data directory relative to project root
        # Assuming backend/utils/allowlist.py -> ../../data/
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent.parent
        data_dir = project_root / "data"

        return str(data_dir / filename)

    def _parse_allowlist_csv(self, text: str) -> pd.DataFrame:
        """Parse allowlist CSV text into a pandas DataFrame.

        Handles both capitalized (Email, Provider) and lowercase (email, provider) column names.

        Parameters
        ----------
        text : str
            Raw CSV text content.

        Returns
        -------
        pd.DataFrame
            DataFrame with provider and email columns, emails lowercased.
        """
        allowlist_df = pd.read_csv(StringIO(text))

        # Normalize column names to lowercase first for consistent handling
        allowlist_df.columns = allowlist_df.columns.str.lower().str.strip()

        # Ensure required columns exist (now checking lowercase)
        if "email" not in allowlist_df.columns:
            error_msg = f"CSV must contain 'email' or 'Email' column. Found columns: {list(allowlist_df.columns)}"
            raise ValueError(error_msg)

        if "provider" not in allowlist_df.columns:
            error_msg = f"CSV must contain 'provider' or 'Provider' column. Found columns: {list(allowlist_df.columns)}"
            raise ValueError(error_msg)

        # Normalize email addresses
        allowlist_df["email"] = allowlist_df["email"].astype(str).str.strip().str.lower()

        # Remove empty emails and NaN values
        allowlist_df = allowlist_df[(allowlist_df["email"].str.len() > 0) & (allowlist_df["email"] != "nan")]

        return allowlist_df[["provider", "email"]].drop_duplicates()

    def _validate_allowlist_data(self, allowlist_df: pd.DataFrame) -> bool:
        """Validate allowlist data using simple pandas checks.

        Performs critical data quality checks on the allowlist DataFrame.

        Parameters
        ----------
        allowlist_df : pd.DataFrame
            The allowlist DataFrame to validate.

        Returns
        -------
        bool
            True if data passes all critical validation checks, False otherwise.

        Note
        ----
        This method implements fail-fast behavior: if validation fails,
        the allowlist data is considered invalid and will not be cached.
        This ensures data quality but may cause temporary service disruption
        if the allowlist file becomes corrupted.
        """
        try:
            # 1. Check required columns exist
            required_columns = ["provider", "email"]
            if not all(col in allowlist_df.columns for col in required_columns):
                logger.error("Missing required columns. Expected: %s, got: %s", required_columns, list(allowlist_df.columns))
            # 2. Check for null values in critical columns
            elif allowlist_df[required_columns].isna().any().any():
                logger.error("Found null values in required columns")
            # 3. Check at least one row exists
            elif len(allowlist_df) == 0:
                logger.error("Allowlist data is empty")
            # 4. Check for duplicate emails
            elif allowlist_df["email"].duplicated().any():
                logger.error("Found duplicate emails in allowlist data")
            # 5. Validate email format (basic regex check)
            else:
                email_pattern = r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"
                invalid_emails = ~allowlist_df["email"].str.match(email_pattern)
                if invalid_emails.any():
                    invalid_count = invalid_emails.sum()
                    logger.error("Found %d emails with invalid format", invalid_count)
                    return False
                # 6. Check emails are from justice.gov.uk domain (allow localhost for dev)
                else:
                    allowed_domains = ["@justice.gov.uk", "@localhost.com"]
                    valid_domain = allowlist_df["email"].apply(
                        lambda email: any(email.endswith(domain) for domain in allowed_domains)
                    )
                    if not valid_domain.all():
                        invalid_count = (~valid_domain).sum()
                        logger.error("Found %d emails not from allowed domains (@justice.gov.uk or @localhost.com)", invalid_count)
                        return False
                    else:
                        logger.info("Allowlist data validation passed. Validated %d rows.", len(allowlist_df))
                        return True

        except Exception:
            logger.exception("Allowlist data validation error")
            return False

    async def is_user_allowlisted(
        self,
        email: str | None,
        connection_string: str,
        container: str,
        blob_name: str
    ) -> bool:
        """Check if a user's email is allowlisted with caching.

        Parameters
        ----------
        email : Optional[str]
            The email address to check.
        connection_string : str
            Azure Storage connection string.
        container : str
            Blob container name.
        blob_name : str
            Blob name within the container.

        Returns
        -------
        bool
            True if the email is allowlisted, False otherwise.
            Returns False if allowlist data cannot be loaded (fail-safe).

        Note
        ----
        This method implements a fail-safe approach: if the allowlist cannot
        be loaded after retries, it returns False (deny access) rather than
        raising an exception. This ensures the application remains secure
        even when the allowlist service is unavailable.
        """
        if not email:
            return False

        normalized_email = email.lower().strip()

        # Check user-specific cache first
        if normalized_email in self._user_status and self._is_valid():
            return self._user_status[normalized_email]

        # Load allowlist data if needed
        if not self._is_valid():
            async with self._lock:
                if not self._is_valid():
                    try:
                        self._allowlist_data = await self._load_allowlist_data(
                            connection_string, container, blob_name
                        )
                        self._expires_at = time.time() + self._ttl_seconds
                        # Clear user cache when allowlist data refreshes
                        self._user_status.clear()
                    except Exception as e:
                        # Log the error but don't raise - fail-safe to deny access
                        logger.warning("Failed to load allowlist data: %s", e)
                        # Cache a denial for this user to avoid repeated failed attempts
                        self._user_status[normalized_email] = False
                        return False

        # Check against allowlist data
        is_allowlisted = normalized_email in self._allowlist_data["email"].to_numpy()

        # Cache the result
        self._user_status[normalized_email] = is_allowlisted

        return is_allowlisted


# Factory function to create cache instance
def create_allowlist_cache(ttl_seconds: int = 300) -> UserAllowlistCache:
    """Create a new allowlist cache instance.

    Parameters
    ----------
    ttl_seconds : int
        Time-to-live for cache entries in seconds.

    Returns
    -------
    UserAllowlistCache
        New cache instance.
    """
    return UserAllowlistCache(ttl_seconds)
