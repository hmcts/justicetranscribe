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
                content = await self._download_blob_content(connection_string, container, blob_name)
                allowlist_df = self._parse_and_validate_content(content, blob_name)
                logger.info("Successfully loaded allowlist from Azure: %s", blob_name)
                return allowlist_df  # noqa: TRY300 - Return immediately on success, not after all retries
            except Exception as e:
                last_exception = e
                logger.warning("Attempt %d/%d failed: %s", attempt + 1, max_retries, e)
                if attempt < max_retries - 1:  # Not the last attempt
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        # All Azure attempts failed - try local fallback in development
        return await self._try_local_fallback(blob_name, last_exception)

    async def _download_blob_content(
        self,
        connection_string: str,
        container: str,
        blob_name: str
    ) -> bytes:
        """Download blob content using AsyncBlobServiceClient with fallback."""
        try:
            # Use single client for both existence check and download
            async with AsyncBlobServiceClient.from_connection_string(connection_string) as blob_service_client:
                blob_client = blob_service_client.get_blob_client(
                    container=container, blob=blob_name
                )

                # Check if blob exists first
                if not await blob_client.exists():
                    error_msg = "Blob not found"
                    raise FileNotFoundError(error_msg) from None

                # Download using the same client
                stream = await blob_client.download_blob()
                return await stream.readall()

        except Exception as azure_utils_error:
            logger.warning("AsyncBlobServiceClient failed, falling back to direct pattern: %s", azure_utils_error)

            # Fallback to existing working pattern
            blob_service_client = AsyncBlobServiceClient.from_connection_string(connection_string)
            async with blob_service_client:
                blob_client = blob_service_client.get_blob_client(
                    container=container, blob=blob_name
                )
                stream = await blob_client.download_blob()
                return await stream.readall()

    def _parse_and_validate_content(self, content: bytes, blob_name: str) -> pd.DataFrame:  # noqa: ARG002
        """Parse blob content and validate the resulting DataFrame."""
        # Parse and validate - handle encoding at byte level
        allowlist_df = self._parse_allowlist_csv_from_bytes(content)

        # Clean and normalize the data first
        allowlist_df = self._clean_and_normalize_dataframe(allowlist_df)

        # Then validate the cleaned data
        is_valid, cleaned_df = self._validate_allowlist_data(allowlist_df)
        if not is_valid:
            error_msg = "Allowlist data failed validation checks"
            raise ValueError(error_msg)

        # Use the cleaned data
        allowlist_df = cleaned_df

        return allowlist_df

    async def _try_local_fallback(self, blob_name: str, last_exception: Exception) -> pd.DataFrame:
        """Try local file fallback for development environment."""
        if os.getenv("ENVIRONMENT", "").lower() != "local":
            raise last_exception

        logger.warning("Azure blob not found. Attempting local file fallback for development...")
        try:
            local_file = self._get_local_fallback_path(blob_name)
            if Path(local_file).exists():
                # Use aiofiles for async file operations
                async with aiofiles.open(local_file, mode="rb") as f:
                    content = await f.read()
                allowlist_df = self._parse_allowlist_csv_from_bytes(content)
                # Clean and normalize the data first
                allowlist_df = self._clean_and_normalize_dataframe(allowlist_df)
                # Then validate the cleaned data
                is_valid, cleaned_df = self._validate_allowlist_data(allowlist_df)
                if is_valid:
                    logger.info("✅ Using local fallback file: %s", local_file)
                    return cleaned_df
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

    def _parse_allowlist_csv_from_bytes(self, content: bytes) -> pd.DataFrame:
        """Parse allowlist CSV from bytes with proper encoding fallback.

        Parameters
        ----------
        content : bytes
            Raw CSV content as bytes.

        Returns
        -------
        pd.DataFrame
            DataFrame with provider and email columns, emails lowercased.
        """
        try:
            # Try UTF-8 first
            text = content.decode("utf-8")
            allowlist_df = pd.read_csv(StringIO(text))
        except UnicodeDecodeError:
            # Fallback to cp1252 encoding if UTF-8 fails
            logger.warning("UTF-8 decoding failed, trying cp1252 encoding")
            try:
                text = content.decode("cp1252")
                allowlist_df = pd.read_csv(StringIO(text))
            except Exception:
                # If both fail, try with explicit column names
                logger.warning("cp1252 also failed, trying with explicit column names")
                text = content.decode("cp1252", errors="ignore")  # Use errors="ignore" as last resort
                allowlist_df = pd.read_csv(StringIO(text), names=["email", "provider"])

        # Clean up the DataFrame
        return self._clean_and_normalize_dataframe(allowlist_df)

    def _parse_allowlist_csv(self, text: str) -> pd.DataFrame:
        """Parse allowlist CSV text into a pandas DataFrame.

        Handles both capitalized (Email, Provider) and lowercase (email, provider) column names.
        Cleans up records that begin with newline characters.

        Parameters
        ----------
        text : str
            Raw CSV text content.

        Returns
        -------
        pd.DataFrame
            DataFrame with provider and email columns, emails lowercased.
        """
        # Clean up text: remove leading newlines from lines and normalize line endings
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            # Remove leading newline characters and other whitespace
            cleaned_line = line.lstrip("\n\r\t ").rstrip("\n\r\t ")
            if cleaned_line:  # Only keep non-empty lines
                cleaned_lines.append(cleaned_line)

        cleaned_text = "\n".join(cleaned_lines)

        # Parse CSV
        allowlist_df = pd.read_csv(StringIO(cleaned_text))

        # Clean up the DataFrame
        return self._clean_and_normalize_dataframe(allowlist_df)

    def _clean_and_normalize_dataframe(self, allowlist_df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize the allowlist DataFrame.

        Parameters
        ----------
        allowlist_df : pd.DataFrame
            Raw DataFrame from CSV parsing.

        Returns
        -------
        pd.DataFrame
            Cleaned and normalized DataFrame with provider and email columns.
        """
        # Normalize column names to lowercase first for consistent handling
        allowlist_df.columns = allowlist_df.columns.str.lower().str.strip()

        # Check for email column (required) - handle "Email" vs "email" gracefully
        if "email" not in allowlist_df.columns:
            error_msg = f"CSV must contain 'email' or 'Email' column. Found columns: {list(allowlist_df.columns)}"
            raise ValueError(error_msg)

        # Check for provider column (optional) - warn if missing
        if "provider" not in allowlist_df.columns:
            logger.warning("CSV missing 'provider' or 'Provider' column. Found columns: %s", list(allowlist_df.columns))
            # Add a default provider column if missing
            allowlist_df["provider"] = "unknown"

        # Normalize email addresses and clean up any remaining newline characters
        allowlist_df["email"] = allowlist_df["email"].astype(str).str.strip().str.lower()
        allowlist_df["email"] = allowlist_df["email"].str.replace(r"^\n+", "", regex=True)  # Remove leading newlines
        allowlist_df["email"] = allowlist_df["email"].str.replace(r"\n+$", "", regex=True)  # Remove trailing newlines

        # Remove empty emails and NaN values
        allowlist_df = allowlist_df[(allowlist_df["email"].str.len() > 0) & (allowlist_df["email"] != "nan")]

        # Handle case-insensitive duplicate removal with logging
        original_count = len(allowlist_df)

        # Check for duplicates before removing them (case-insensitive email matching)
        # Use keep='first' to identify only the duplicate rows (excluding first occurrence)
        duplicates_mask = allowlist_df.duplicated(subset=["email"], keep="first")
        duplicate_count = duplicates_mask.sum()

        if duplicate_count > 0:
            # Get the unique duplicate emails (excluding first occurrence)
            duplicate_emails = allowlist_df[duplicates_mask]["email"].unique()
            logger.warning(
                "Found %d duplicate email entries in allowlist (case-insensitive). "
                "Removing %d duplicate rows, keeping first occurrence. "
                "Duplicate emails: %s",
                duplicate_count,
                duplicate_count,
                ", ".join(duplicate_emails)
            )

        # Remove duplicates, keeping first occurrence (case-insensitive email matching)
        allowlist_df = allowlist_df.drop_duplicates(subset=["email"], keep="first")

        final_count = len(allowlist_df)
        if duplicate_count > 0:
            logger.info(
                "Allowlist deduplication complete. Original: %d rows, Final: %d rows, "
                "Duplicates removed: %d",
                original_count,
                final_count,
                original_count - final_count
            )

        # Return both columns (provider is always present after normalization)
        return allowlist_df[["provider", "email"]]

    def _validate_allowlist_data(self, allowlist_df: pd.DataFrame) -> tuple[bool, pd.DataFrame]:
        """Validate allowlist data with resilient error handling.

        Performs data quality checks and cleaning on the allowlist DataFrame.
        Logs warnings for data quality issues but only fails if no valid rows remain.

        Parameters
        ----------
        allowlist_df : pd.DataFrame
            The allowlist DataFrame to validate and clean.

        Returns
        -------
        tuple[bool, pd.DataFrame]
            Tuple of (success, cleaned_dataframe). Success is True if there are valid rows after cleaning.
        """
        # Store original DataFrame for error cases
        try:
            original_df = allowlist_df.copy()
        except AttributeError:
            # Fallback for mock objects or DataFrames without copy method
            original_df = allowlist_df

        try:
            original_count = len(allowlist_df)

            # 1. Check required columns exist - handle gracefully
            if not self._check_required_columns(allowlist_df):
                return False, allowlist_df

            # 2. Handle null values - log warning and filter out
            allowlist_df = self._filter_null_values(allowlist_df)
            if len(allowlist_df) == 0:
                logger.error("No valid rows remaining after filtering null values")
                return False, allowlist_df

            # 3. Validate email format - log warning and filter out invalid emails
            allowlist_df = self._filter_invalid_emails(allowlist_df)

            # 4. Check emails are from allowed domains - log warning and filter out invalid domains
            allowlist_df = self._filter_invalid_domains(allowlist_df)

            # 5. Final check - do we have any valid rows left?
            if len(allowlist_df) == 0:
                logger.error("No valid rows remaining after all filtering")
                return False, allowlist_df
            else:
                # 6. Log summary of cleaning
                self._log_cleaning_summary(allowlist_df, original_count)
                return True, allowlist_df

        except Exception:
            logger.exception("Allowlist data validation error")
            return False, original_df

    def _check_required_columns(self, allowlist_df: pd.DataFrame) -> bool:
        """Check if required columns exist."""
        # Only email is truly required
        if "email" not in allowlist_df.columns:
            logger.error("Missing required 'email' column. Found columns: %s", list(allowlist_df.columns))
            return False

        # Provider is optional - warn if missing
        if "provider" not in allowlist_df.columns:
            logger.warning("Missing optional 'provider' column. Found columns: %s", list(allowlist_df.columns))

        return True

    def _filter_null_values(self, allowlist_df: pd.DataFrame) -> pd.DataFrame:
        """Filter out rows with null values in provider or email columns."""
        # Handle null values in provider column (if it exists)
        if "provider" in allowlist_df.columns and allowlist_df["provider"].isna().any():
            null_provider_count = allowlist_df["provider"].isna().sum()
            logger.warning("Found %d rows with null provider values, filtering them out", null_provider_count)
            allowlist_df = allowlist_df.dropna(subset=["provider"])

        # Handle null values in email column (required)
        if allowlist_df["email"].isna().any():
            null_email_count = allowlist_df["email"].isna().sum()
            logger.warning("Found %d rows with null email values, filtering them out", null_email_count)
            allowlist_df = allowlist_df.dropna(subset=["email"])

        return allowlist_df

    def _filter_invalid_emails(self, allowlist_df: pd.DataFrame) -> pd.DataFrame:
        """Filter out rows with invalid email formats."""
        email_pattern = r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"
        invalid_emails_mask = ~allowlist_df["email"].str.match(email_pattern)
        if invalid_emails_mask.any():
            invalid_count = invalid_emails_mask.sum()
            invalid_emails = allowlist_df[invalid_emails_mask]["email"].tolist()
            logger.warning("Found %d emails with invalid format, filtering them out: %s",
                         invalid_count, ", ".join(invalid_emails[:10]))  # Show first 10
            allowlist_df = allowlist_df[~invalid_emails_mask]
        return allowlist_df

    def _filter_invalid_domains(self, allowlist_df: pd.DataFrame) -> pd.DataFrame:
        """Filter out rows with emails from disallowed domains."""
        allowed_domains = ["@justice.gov.uk", "@localhost.com"]
        valid_domain_mask = allowlist_df["email"].apply(
            lambda email: any(email.endswith(domain) for domain in allowed_domains)
        )
        if not valid_domain_mask.all():
            invalid_domain_count = (~valid_domain_mask).sum()
            invalid_domain_emails = allowlist_df[~valid_domain_mask]["email"].tolist()
            logger.warning("Found %d emails not from allowed domains (@justice.gov.uk or @localhost.com), filtering them out: %s",
                         invalid_domain_count, ", ".join(invalid_domain_emails[:10]))  # Show first 10
            allowlist_df = allowlist_df[valid_domain_mask]
        return allowlist_df

    def _log_cleaning_summary(self, allowlist_df: pd.DataFrame, original_count: int) -> None:
        """Log summary of data cleaning operations."""
        final_count = len(allowlist_df)
        if final_count < original_count:
            logger.info("Allowlist data cleaned: %d rows removed, %d valid rows remaining",
                       original_count - final_count, final_count)
        else:
            logger.info("Allowlist data validation passed. %d rows validated.", final_count)

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


# Global cache instance - singleton pattern
_global_cache: UserAllowlistCache | None = None


def get_allowlist_cache(ttl_seconds: int = 300) -> UserAllowlistCache:
    """
    Get the global allowlist cache instance (singleton pattern).

    This ensures that all requests share the same cache instance,
    providing proper caching behavior and avoiding repeated Azure
    Blob Storage calls.

    Parameters
    ----------
    ttl_seconds : int
        Time-to-live for cache entries in seconds. Only used on first creation.

    Returns
    -------
    UserAllowlistCache
        The global cache instance.
    """
    # Use module-level variable with proper access pattern
    # PLW0603: Using global for singleton pattern is acceptable here
    global _global_cache  # noqa: PLW0603
    if _global_cache is None:
        _global_cache = UserAllowlistCache(ttl_seconds)
    return _global_cache


def create_allowlist_cache(ttl_seconds: int = 300) -> UserAllowlistCache:
    """
    Create a new allowlist cache instance.

    Note: This function is kept for backward compatibility but should
    generally be avoided in favor of get_allowlist_cache() for shared
    caching behavior.

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
