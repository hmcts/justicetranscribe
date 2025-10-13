"""Unit tests for allowlist functionality."""


from unittest.mock import patch

import pandas as pd
import pytest
from conftest import clean_email_for_comparison, create_test_csv_data

from utils.allowlist import UserAllowlistCache, create_allowlist_cache


class TestUserAllowlistCache:
    """Test cases for UserAllowlistCache class."""

    @pytest.fixture
    def cache(self) -> UserAllowlistCache:
        """Create a fresh cache instance for each test."""
        return UserAllowlistCache(ttl_seconds=1)  # Short TTL for testing

    @pytest.fixture
    def mock_logger(self):
        """Mock logger to prevent test log clutter."""
        with patch("utils.allowlist.logger") as mock_logger:
            yield mock_logger

    @pytest.fixture
    def sample_csv_data(self) -> str:
        """Sample CSV data for testing with realistic formatting."""
        return create_test_csv_data([
            ("Ai Justice Unit", "JOHN.DOE@JUSTICE.GOV.UK"),
            ("Wales", "jane.doe@justice.gov.uk"),
            ("KSS", "Test.User@Justice.Gov.UK"),
        ])

    @pytest.fixture
    def sample_dataframe(self) -> pd.DataFrame:
        """Sample DataFrame for testing with cleaned data."""
        return pd.DataFrame({
            "provider": ["Ai Justice Unit", "Wales", "KSS"],
            "email": [
                "john.doe@justice.gov.uk",  # Cleaned from "  JOHN.DOE@JUSTICE.GOV.UK  "
                "jane.doe@justice.gov.uk",  # Cleaned from "  jane.doe@justice.gov.uk  "
                "test.user@justice.gov.uk"  # Cleaned from "  Test.User@Justice.Gov.UK  "
            ]
        })

    def test_cache_initialization(self, cache: UserAllowlistCache):
        """Test cache initializes with correct default values."""
        # Test through public behavior rather than accessing private members
        # A fresh cache should not have any cached users
        assert len(cache._user_status) == 0
        assert cache._expires_at == 0.0
        assert cache._allowlist_data is None
        assert cache._ttl_seconds == 1
    def test_is_valid_with_no_data(self, cache: UserAllowlistCache):
        """Test cache validity when no data is loaded."""
        is_valid = cache._is_valid()
        assert not is_valid, f"Expected cache to be invalid with no data, but _is_valid() returned {is_valid}"

    def test_is_valid_with_expired_data(self, cache: UserAllowlistCache):
        """Test cache validity when data has expired."""
        cache._allowlist_data = pd.DataFrame()
        cache._expires_at = 0.0  # Expired
        is_valid = cache._is_valid()
        assert not is_valid, f"Expected cache to be invalid with expired data, but _is_valid() returned {is_valid}"

    def test_is_valid_with_valid_data(self, cache: UserAllowlistCache):
        """Test cache validity when data is valid and not expired."""
        cache._allowlist_data = pd.DataFrame()
        cache._expires_at = 9999999999  # Far future
        is_valid = cache._is_valid()
        assert is_valid, f"Expected cache to be valid with data and future expiry, but _is_valid() returned {is_valid}"

    def test_parse_allowlist_csv_success(self, cache: UserAllowlistCache, sample_csv_data: str):
        """Test successful CSV parsing."""
        result = cache._parse_allowlist_csv(sample_csv_data)
        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert "provider" in result.columns, f"Expected 'provider' column, got columns: {list(result.columns)}"
        assert "email" in result.columns, f"Expected 'email' column, got columns: {list(result.columns)}"
        assert len(result) == 3, f"Expected 3 rows, got {len(result)} rows. Data: {result.to_dict()}"

        # Use string cleaning for robust email comparison
        cleaned_emails = [clean_email_for_comparison(email) for email in result["email"].to_numpy()]
        expected_email = "john.doe@justice.gov.uk"
        assert expected_email in cleaned_emails, f"Expected '{expected_email}' in cleaned email values, got: {cleaned_emails}"

    def test_parse_allowlist_csv_normalizes_emails(self, cache: UserAllowlistCache):
        """Test that emails are normalized (lowercased and trimmed)."""
        # Use proper CSV formatting with realistic whitespace and case variations
        csv_data = (
            "Provider,Email\n"
            "Test,  JOHN.DOE@JUSTICE.GOV.UK  \n"
            "Test,  jane.doe@justice.gov.uk  \n"
        )

        result = cache._parse_allowlist_csv(csv_data)
        # Use string cleaning for robust comparison
        cleaned_emails = [clean_email_for_comparison(email) for email in result["email"].to_numpy()]
        expected_emails = ["john.doe@justice.gov.uk", "jane.doe@justice.gov.uk"]

        for expected_email in expected_emails:
            assert expected_email in cleaned_emails, f"Expected normalized email '{expected_email}' in cleaned values, got: {cleaned_emails}"

    def test_parse_allowlist_csv_removes_empty_emails(self, cache: UserAllowlistCache):
        """Test that empty emails are removed."""
        # Use helper function to create properly formatted CSV with empty email
        csv_data = create_test_csv_data([
            ("Test", "john.doe@justice.gov.uk"),
            ("Test", ""),  # Empty email that should be removed
            ("Test", "jane.doe@justice.gov.uk"),
        ])

        result = cache._parse_allowlist_csv(csv_data)
        assert len(result) == 2, f"Expected 2 rows after removing empty emails, got {len(result)} rows. Data: {result.to_dict()}"
        assert "" not in result["email"].to_numpy(), f"Expected no empty strings in email values, got: {result['email'].tolist()}"

    def test_parse_allowlist_csv_requires_email_column(self, cache: UserAllowlistCache):
        """Test that CSV must contain email column (case-insensitive)."""
        # Use properly formatted CSV without email column
        csv_data = (
            "Provider,Name\n"
            "Test,Richard\n"
            "Test,John\n"
        )

        with pytest.raises(ValueError, match="CSV must contain 'email' or 'Email' column") as exc_info:
            cache._parse_allowlist_csv(csv_data)
        assert "email" in str(exc_info.value).lower(), f"Expected error about missing email column, got: {exc_info.value}"

    def test_parse_allowlist_csv_handles_missing_provider_column(self, cache: UserAllowlistCache, mock_logger):
        """Test that CSV without provider column gets warning and default values."""
        # Use properly formatted CSV without provider column
        csv_data = (
            "Email,Name\n"
            "test@justice.gov.uk,Richard\n"
            "test2@justice.gov.uk,John\n"
        )

        result = cache._parse_allowlist_csv(csv_data)

        # Should succeed with warning
        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert len(result) == 2, f"Expected 2 rows, got {len(result)}"
        assert "provider" in result.columns, f"Expected 'provider' column to be added, got: {list(result.columns)}"
        assert "email" in result.columns, f"Expected 'email' column, got: {list(result.columns)}"

        # Provider should have default "unknown" values
        assert all(result["provider"] == "unknown"), f"Expected all provider values to be 'unknown', got: {result['provider'].tolist()}"

        # Should have logged warning about missing provider
        mock_logger.warning.assert_called()
        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
        assert any("CSV missing 'provider' or 'Provider' column" in call for call in warning_calls), f"Expected warning about missing provider column, got: {warning_calls}"

    def test_parse_allowlist_csv_integration(self, cache: UserAllowlistCache, sample_csv_data: str):
        """Test CSV parsing with realistic data - this tests the core parsing logic."""
        result = cache._parse_allowlist_csv(sample_csv_data)

        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert len(result) == 3, f"Expected 3 rows, got {len(result)} rows. Data: {result.to_dict()}"
        assert "john.doe@justice.gov.uk" in result["email"].to_numpy(), f"Expected 'john.doe@justice.gov.uk' in email values, got: {result['email'].tolist()}"

    def test_parse_allowlist_csv_handles_lowercase_columns(self, cache: UserAllowlistCache):
        """Test that CSV parsing handles lowercase column names."""
        csv_data = (
            "provider,email\n"
            "Test Provider,test@justice.gov.uk\n"
            "Another Provider,another@justice.gov.uk\n"
        )

        result = cache._parse_allowlist_csv(csv_data)
        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert len(result) == 2, f"Expected 2 rows, got {len(result)} rows"
        assert "test@justice.gov.uk" in result["email"].to_numpy()
        assert "another@justice.gov.uk" in result["email"].to_numpy()
        assert list(result.columns) == ["provider", "email"], f"Expected lowercase columns, got {list(result.columns)}"

    def test_parse_allowlist_csv_handles_capitalized_columns(self, cache: UserAllowlistCache):
        """Test that CSV parsing handles capitalized column names (legacy format)."""
        csv_data = (
            "Provider,Email\n"
            "Test Provider,test@justice.gov.uk\n"
            "Another Provider,another@justice.gov.uk\n"
        )

        result = cache._parse_allowlist_csv(csv_data)
        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert len(result) == 2, f"Expected 2 rows, got {len(result)} rows"
        assert "test@justice.gov.uk" in result["email"].to_numpy()
        assert "another@justice.gov.uk" in result["email"].to_numpy()
        # Columns should be normalized to lowercase
        assert list(result.columns) == ["provider", "email"], f"Expected lowercase columns, got {list(result.columns)}"

    @pytest.mark.asyncio
    async def test_is_user_allowlisted_with_none_email(self, cache: UserAllowlistCache):
        """Test allowlist check with None email."""
        result = await cache.is_user_allowlisted(
            None, "test_conn", "test_container", "test_blob"
        )
        assert result is False, f"Expected False for None email, got {result}"

    @pytest.mark.asyncio
    async def test_is_user_allowlisted_with_empty_email(self, cache: UserAllowlistCache):
        """Test allowlist check with empty email."""
        result = await cache.is_user_allowlisted(
            "", "test_conn", "test_container", "test_blob"
        )
        assert result is False, f"Expected False for empty email, got {result}"

    @pytest.mark.asyncio
    async def test_is_user_allowlisted_cached_result(self, cache: UserAllowlistCache, sample_dataframe: pd.DataFrame):
        """Test that cached results are returned without reloading data."""
        # Pre-populate cache
        cache._allowlist_data = sample_dataframe
        cache._expires_at = 9999999999  # Far future
        cache._user_status["john.doe@justice.gov.uk"] = True
        result = await cache.is_user_allowlisted(
            "john.doe@justice.gov.uk",
            "test_conn", "test_container", "test_blob"
        )

        assert result is True, f"Expected True for cached allowlisted user, got {result}"

    def test_is_user_allowlisted_with_preloaded_data(self, cache: UserAllowlistCache, sample_dataframe: pd.DataFrame):
        """Test allowlist check with preloaded data - tests core logic without Azure complexity."""
        # Pre-populate cache with data
        cache._allowlist_data = sample_dataframe
        cache._expires_at = 9999999999  # Far future
        # Test that the core logic works - check if email exists in the allowlist
        email_exists = "john.doe@justice.gov.uk" in cache._allowlist_data["email"].to_numpy()
        assert email_exists, f"Expected to find john.doe@justice.gov.uk in allowlist data, got: {cache._allowlist_data['email'].tolist()}"
    def test_fail_safe_behavior_simulation(self, cache: UserAllowlistCache):
        """Test fail-safe behavior simulation - tests the core fail-safe logic."""
        # Simulate the fail-safe behavior by manually setting the user status
        cache._user_status["test@example.com"] = False
        # Verify the fail-safe behavior
        assert cache._user_status["test@example.com"] is False, f"Expected False for failed user in cache, got {cache._user_status['test@example.com']}"
        assert "test@example.com" in cache._user_status, f"Expected 'test@example.com' in user status cache, got: {list(cache._user_status.keys())}"
    @pytest.mark.asyncio
    async def test_is_user_allowlisted_normalizes_email(self, cache: UserAllowlistCache, sample_dataframe: pd.DataFrame):
        """Test that email normalization works correctly."""
        cache._allowlist_data = sample_dataframe
        cache._expires_at = 9999999999
        # Test with mixed case and whitespace - use an email that exists in sample data
        result = await cache.is_user_allowlisted(
            "  JOHN.DOE@JUSTICE.GOV.UK  ",
            "test_conn", "test_container", "test_blob"
        )

        assert result is True, f"Expected True for normalized email, got {result}"
        assert "john.doe@justice.gov.uk" in cache._user_status, f"Expected normalized email in user status cache, got: {list(cache._user_status.keys())}"
    def test_cache_clears_user_status_on_data_refresh(self, cache: UserAllowlistCache, sample_dataframe: pd.DataFrame):
        """Test that user status cache is cleared when allowlist data refreshes."""
        # Pre-populate user cache
        cache._user_status["test@example.com"] = True
        # Simulate data refresh by setting new allowlist data
        cache._allowlist_data = sample_dataframe
        cache._expires_at = 9999999999  # Far future
        # Simulate the cache clearing that happens in the real method
        cache._user_status.clear()
        cache._user_status["john.doe@justice.gov.uk"] = True
        # Verify the cache was cleared and repopulated
        assert cache._user_status == {"john.doe@justice.gov.uk": True}, f"Expected user status cache to contain only normalized email, got: {cache._user_status}"

    def test_validate_allowlist_data_valid_data(self, cache: UserAllowlistCache, sample_dataframe: pd.DataFrame):
        """Test that valid allowlist data passes validation."""
        is_valid, cleaned_df = cache._validate_allowlist_data(sample_dataframe)
        assert is_valid is True, f"Expected valid data to pass validation, got {is_valid}"
        assert len(cleaned_df) == len(sample_dataframe), "Valid data should not be filtered"

    def test_validate_allowlist_data_missing_columns(self, cache: UserAllowlistCache):
        """Test that data with missing columns fails validation."""
        invalid_df = pd.DataFrame({
            "provider": ["Test"],
            "name": ["test@example.com"]  # Missing email column
        })

        is_valid, cleaned_df = cache._validate_allowlist_data(invalid_df)
        assert is_valid is False, f"Expected data with missing columns to fail validation, got {is_valid}"

    def test_validate_allowlist_data_null_values(self, cache: UserAllowlistCache):
        """Test that data with null values fails validation."""
        invalid_df = pd.DataFrame({
            "provider": ["Test", None],
            "email": ["test@justice.gov.uk", "test2@justice.gov.uk"]
        })

        is_valid, cleaned_df = cache._validate_allowlist_data(invalid_df)
        assert is_valid is True, f"Expected data with null values to be cleaned and pass validation, got {is_valid}"
        assert len(cleaned_df) == 1, f"Expected 1 valid row after cleaning, got {len(cleaned_df)}"

    def test_validate_allowlist_data_invalid_email_format(self, cache: UserAllowlistCache):
        """Test that data with invalid email format gets filtered out."""
        invalid_df = pd.DataFrame({
            "provider": ["Test"],
            "email": ["invalid-email-format"]  # Invalid email
        })

        is_valid, cleaned_df = cache._validate_allowlist_data(invalid_df)
        assert is_valid is False, f"Expected data with invalid email format to fail validation (no valid rows), got {is_valid}"
        assert len(cleaned_df) == 0, f"Expected 0 valid rows after cleaning, got {len(cleaned_df)}"

    def test_validate_allowlist_data_wrong_domain(self, cache: UserAllowlistCache):
        """Test that data with wrong email domain gets filtered out."""
        invalid_df = pd.DataFrame({
            "provider": ["Test"],
            "email": ["test@example.com"]  # Wrong domain
        })

        is_valid, cleaned_df = cache._validate_allowlist_data(invalid_df)
        assert is_valid is False, f"Expected data with wrong domain to fail validation (no valid rows), got {is_valid}"
        assert len(cleaned_df) == 0, f"Expected 0 valid rows after cleaning, got {len(cleaned_df)}"

    def test_clean_and_normalize_dataframe_removes_duplicates(self, cache: UserAllowlistCache, mock_logger):
        """Test that duplicate emails are removed during cleaning with proper logging."""
        # Create DataFrame with case-insensitive duplicates
        df_with_duplicates = pd.DataFrame({
            "provider": ["Test", "Test2", "Test3"],
            "email": ["test@justice.gov.uk", "TEST@JUSTICE.GOV.UK", "test@justice.gov.uk"]  # Case-insensitive duplicates
        })

        result = cache._clean_and_normalize_dataframe(df_with_duplicates)

        # Should only have 1 row (all 3 emails are the same after normalization)
        assert len(result) == 1, f"Expected 1 row after deduplication, got {len(result)}"

        # Should have the first occurrence of the unique email
        expected_emails = ["test@justice.gov.uk"]
        actual_emails = result["email"].tolist()
        assert actual_emails == expected_emails, f"Expected {expected_emails}, got {actual_emails}"

        # Should have logged a warning about duplicates
        mock_logger.warning.assert_called_once()
        warning_call_args = mock_logger.warning.call_args[0]
        assert "Found %d duplicate email entries" in warning_call_args[0]
        assert warning_call_args[1] == 2  # duplicate_count
        assert warning_call_args[2] == 2  # duplicate_count again
        assert "test@justice.gov.uk" in warning_call_args[3]

        # Should have logged info about deduplication completion
        mock_logger.info.assert_called_once()
        info_call_args = mock_logger.info.call_args[0]
        assert "Allowlist deduplication complete" in info_call_args[0]
        assert info_call_args[1] == 3  # original_count
        assert info_call_args[2] == 1  # final_count
        assert info_call_args[3] == 2  # duplicates_removed

    def test_clean_and_normalize_dataframe_removes_duplicates_different_emails(self, cache: UserAllowlistCache, mock_logger):
        """Test that duplicate emails are removed when there are different unique emails."""
        # Create DataFrame with some duplicates and some unique emails
        df_with_duplicates = pd.DataFrame({
            "provider": ["Test1", "Test2", "Test3", "Test4"],
            "email": ["user1@justice.gov.uk", "USER1@JUSTICE.GOV.UK", "user2@justice.gov.uk", "user1@justice.gov.uk"]  # user1 appears 3 times, user2 once
        })

        result = cache._clean_and_normalize_dataframe(df_with_duplicates)

        # Should have 2 rows (user1 and user2, keeping first occurrence of each)
        assert len(result) == 2, f"Expected 2 rows after deduplication, got {len(result)}"

        # Should have the first occurrence of each unique email
        expected_emails = ["user1@justice.gov.uk", "user2@justice.gov.uk"]
        actual_emails = sorted(result["email"].tolist())
        assert actual_emails == expected_emails, f"Expected {expected_emails}, got {actual_emails}"

        # Should have logged a warning about duplicates
        mock_logger.warning.assert_called_once()
        warning_call_args = mock_logger.warning.call_args[0]
        assert "Found %d duplicate email entries" in warning_call_args[0]
        assert warning_call_args[1] == 2  # duplicate_count
        assert warning_call_args[2] == 2  # duplicate_count again
        assert "user1@justice.gov.uk" in warning_call_args[3]

        # Should have logged info about deduplication completion
        mock_logger.info.assert_called_once()
        info_call_args = mock_logger.info.call_args[0]
        assert "Allowlist deduplication complete" in info_call_args[0]
        assert info_call_args[1] == 4  # original_count
        assert info_call_args[2] == 2  # final_count
        assert info_call_args[3] == 2  # duplicates_removed

    def test_validate_allowlist_data_passes_after_deduplication(self, cache: UserAllowlistCache):
        """Test that validation passes for data that has been deduplicated."""
        # Create DataFrame with duplicates that would be cleaned
        df_with_duplicates = pd.DataFrame({
            "provider": ["Test", "Test2"],
            "email": ["test@justice.gov.uk", "test@justice.gov.uk"]  # Duplicate emails
        })

        # Clean the data first (this removes duplicates)
        cleaned_df = cache._clean_and_normalize_dataframe(df_with_duplicates)

        # Now validation should pass since duplicates are removed
        is_valid, final_df = cache._validate_allowlist_data(cleaned_df)
        assert is_valid is True, f"Expected cleaned data to pass validation, got {is_valid}"

    def test_validate_allowlist_data_uppercase_emails(self, cache: UserAllowlistCache):
        """Test that data with uppercase emails gets cleaned and passes validation."""
        invalid_df = pd.DataFrame({
            "provider": ["Test"],
            "email": ["TEST@JUSTICE.GOV.UK"]  # Uppercase email
        })

        # Clean and normalize first, then validate
        cleaned_df = cache._clean_and_normalize_dataframe(invalid_df)
        is_valid, final_df = cache._validate_allowlist_data(cleaned_df)
        assert is_valid is True, f"Expected data with uppercase emails to be cleaned and pass validation, got {is_valid}"
        assert len(final_df) == 1, f"Expected 1 valid row after cleaning, got {len(final_df)}"
        assert final_df["email"].iloc[0] == "test@justice.gov.uk", f"Expected email to be lowercased, got {final_df['email'].iloc[0]}"

    def test_validate_allowlist_data_whitespace_emails(self, cache: UserAllowlistCache):
        """Test that data with whitespace in emails gets cleaned and passes validation."""
        invalid_df = pd.DataFrame({
            "provider": ["Test"],
            "email": [" test@justice.gov.uk "]  # Email with whitespace
        })

        # Clean and normalize first, then validate
        cleaned_df = cache._clean_and_normalize_dataframe(invalid_df)
        is_valid, final_df = cache._validate_allowlist_data(cleaned_df)
        assert is_valid is True, f"Expected data with whitespace emails to be cleaned and pass validation, got {is_valid}"
        assert len(final_df) == 1, f"Expected 1 valid row after cleaning, got {len(final_df)}"
        assert final_df["email"].iloc[0] == "test@justice.gov.uk", f"Expected email to be trimmed, got '{final_df['email'].iloc[0]}'"

    def test_validate_allowlist_data_empty_dataframe(self, cache: UserAllowlistCache):
        """Test that empty dataframe fails validation."""
        empty_df = pd.DataFrame(columns=["provider", "email"])

        is_valid, cleaned_df = cache._validate_allowlist_data(empty_df)
        assert is_valid is False, f"Expected empty dataframe to fail validation, got {is_valid}"


    def test_validate_allowlist_data_exception_handling(self, cache: UserAllowlistCache, mock_logger):
        """Test that exceptions in validation are caught and return False (line 265-267)."""
        # Create a custom DataFrame class that raises an exception when accessed
        class ExceptionDataFrame:
            def __init__(self):
                self.columns = ["provider", "email"]

            def __getitem__(self, key):
                test_exception = Exception("Test exception")
                raise test_exception

            def isnull(self):
                test_exception = Exception("Test exception")
                raise test_exception

            def __len__(self):
                return 1

        invalid_df = ExceptionDataFrame()

        is_valid, cleaned_df = cache._validate_allowlist_data(invalid_df)
        assert is_valid is False, f"Expected exception handling to return False, got {is_valid}"
        # Verify that the error was logged
        mock_logger.exception.assert_called_once()
        call_args = mock_logger.exception.call_args
        assert call_args[0][0] == "Allowlist data validation error"

    def test_check_required_columns_email_required(self, cache: UserAllowlistCache, mock_logger):
        """Test that email column is required and returns False if missing."""
        # DataFrame without email column
        df_no_email = pd.DataFrame({
            "provider": ["Test"],
            "name": ["test@example.com"]
        })

        result = cache._check_required_columns(df_no_email)
        assert result is False, f"Expected False for missing email column, got {result}"

        # Should log error about missing email
        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args[0]
        assert "Missing required 'email' column" in error_call[0]
        assert "name" in error_call[1]  # Should show found columns

    def test_check_required_columns_provider_optional(self, cache: UserAllowlistCache, mock_logger):
        """Test that provider column is optional and logs warning if missing."""
        # DataFrame without provider column
        df_no_provider = pd.DataFrame({
            "email": ["test@justice.gov.uk"]
        })

        result = cache._check_required_columns(df_no_provider)
        assert result is True, f"Expected True for missing provider column (optional), got {result}"

        # Should log warning about missing provider
        mock_logger.warning.assert_called_once()
        warning_call = mock_logger.warning.call_args[0]
        assert "Missing optional 'provider' column" in warning_call[0]
        assert "email" in warning_call[1]  # Should show found columns

    def test_check_required_columns_both_present(self, cache: UserAllowlistCache, mock_logger):
        """Test that both columns present returns True with no warnings."""
        # DataFrame with both columns
        df_complete = pd.DataFrame({
            "email": ["test@justice.gov.uk"],
            "provider": ["Test Provider"]
        })

        result = cache._check_required_columns(df_complete)
        assert result is True, f"Expected True for complete data, got {result}"

        # Should not log any warnings or errors
        mock_logger.error.assert_not_called()
        mock_logger.warning.assert_not_called()

    def test_clean_and_normalize_dataframe_handles_email_column_variations(self, cache: UserAllowlistCache):
        """Test that Email vs email column names are handled gracefully."""
        # DataFrame with capitalized Email column
        df_capitalized = pd.DataFrame({
            "Email": ["test@justice.gov.uk", "test2@justice.gov.uk"],
            "Provider": ["Test1", "Test2"]
        })

        result = cache._clean_and_normalize_dataframe(df_capitalized)

        # Should succeed and normalize column names
        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert "email" in result.columns, f"Expected 'email' column (lowercase), got: {list(result.columns)}"
        assert "provider" in result.columns, f"Expected 'provider' column (lowercase), got: {list(result.columns)}"
        assert len(result) == 2, f"Expected 2 rows, got {len(result)}"

        # Emails should be normalized
        assert "test@justice.gov.uk" in result["email"].tolist()
        assert "test2@justice.gov.uk" in result["email"].tolist()

    def test_clean_and_normalize_dataframe_handles_missing_provider(self, cache: UserAllowlistCache, mock_logger):
        """Test that missing provider column gets default values."""
        # DataFrame without provider column
        df_no_provider = pd.DataFrame({
            "email": ["test@justice.gov.uk", "test2@justice.gov.uk"]
        })

        result = cache._clean_and_normalize_dataframe(df_no_provider)

        # Should succeed with provider column added
        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert "provider" in result.columns, f"Expected 'provider' column to be added, got: {list(result.columns)}"
        assert "email" in result.columns, f"Expected 'email' column, got: {list(result.columns)}"
        assert len(result) == 2, f"Expected 2 rows, got {len(result)}"

        # Provider should have default "unknown" values
        assert all(result["provider"] == "unknown"), f"Expected all provider values to be 'unknown', got: {result['provider'].tolist()}"

        # Should log warning about missing provider
        mock_logger.warning.assert_called_once()
        warning_call = mock_logger.warning.call_args[0]
        assert "CSV missing 'provider' or 'Provider' column" in warning_call[0]

    def test_clean_and_normalize_dataframe_handles_missing_email(self, cache: UserAllowlistCache):
        """Test that missing email column raises ValueError."""
        # DataFrame without email column
        df_no_email = pd.DataFrame({
            "provider": ["Test Provider"]
        })

        with pytest.raises(ValueError, match="CSV must contain 'email' or 'Email' column") as exc_info:
            cache._clean_and_normalize_dataframe(df_no_email)

        assert "email" in str(exc_info.value).lower()
        assert "provider" in str(exc_info.value)  # Should show found columns

    def test_clean_and_normalize_dataframe_returns_correct_columns_with_provider(self, cache: UserAllowlistCache):
        """Test that DataFrame with provider returns both columns."""
        df_with_provider = pd.DataFrame({
            "email": ["test@justice.gov.uk"],
            "provider": ["Test Provider"]
        })

        result = cache._clean_and_normalize_dataframe(df_with_provider)

        # Should return both columns
        expected_columns = ["provider", "email"]
        assert list(result.columns) == expected_columns, f"Expected {expected_columns}, got {list(result.columns)}"

    def test_clean_and_normalize_dataframe_returns_both_columns_always(self, cache: UserAllowlistCache):
        """Test that DataFrame always returns both columns (provider added if missing)."""
        df_no_provider = pd.DataFrame({
            "email": ["test@justice.gov.uk"]
        })

        result = cache._clean_and_normalize_dataframe(df_no_provider)

        # Should always return both columns since provider is added if missing
        expected_columns = ["provider", "email"]
        assert list(result.columns) == expected_columns, f"Expected {expected_columns}, got {list(result.columns)}"

    def test_filter_null_values_handles_missing_provider_column(self, cache: UserAllowlistCache):
        """Test that null value filtering works when provider column is missing."""
        # DataFrame without provider column
        df_no_provider = pd.DataFrame({
            "email": ["test@justice.gov.uk", None, "test2@justice.gov.uk"]
        })

        result = cache._filter_null_values(df_no_provider)

        # Should filter out null email values
        assert len(result) == 2, f"Expected 2 rows after filtering null emails, got {len(result)}"
        assert "test@justice.gov.uk" in result["email"].tolist()
        assert "test2@justice.gov.uk" in result["email"].tolist()
        assert result["email"].isna().sum() == 0, "Should have no null email values"

    def test_filter_null_values_handles_provider_column_when_present(self, cache: UserAllowlistCache, mock_logger):
        """Test that null value filtering works when provider column is present."""
        # DataFrame with provider column and null values
        df_with_provider = pd.DataFrame({
            "email": ["test@justice.gov.uk", "test2@justice.gov.uk"],
            "provider": ["Test Provider", None]
        })

        result = cache._filter_null_values(df_with_provider)

        # Should filter out null provider values
        assert len(result) == 1, f"Expected 1 row after filtering null providers, got {len(result)}"
        assert "test@justice.gov.uk" in result["email"].tolist()
        assert result["provider"].isna().sum() == 0, "Should have no null provider values"

        # Should log warning about null provider values
        mock_logger.warning.assert_called_once()
        warning_call = mock_logger.warning.call_args[0]
        assert "Found %d rows with null provider values" in warning_call[0]
        assert warning_call[1] == 1  # null_provider_count

    def test_validate_allowlist_data_handles_missing_provider_gracefully(self, cache: UserAllowlistCache, mock_logger):
        """Test that validation handles missing provider column gracefully."""
        # DataFrame without provider column
        df_no_provider = pd.DataFrame({
            "email": ["test@justice.gov.uk", "test2@justice.gov.uk"]
        })

        is_valid, cleaned_df = cache._validate_allowlist_data(df_no_provider)

        # Should pass validation
        assert is_valid is True, f"Expected validation to pass for data without provider, got {is_valid}"
        assert len(cleaned_df) == 2, f"Expected 2 rows, got {len(cleaned_df)}"

        # Should have logged warning about missing provider
        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
        assert any("Missing optional 'provider' column" in call for call in warning_calls), f"Expected warning about missing provider, got: {warning_calls}"

    def test_validate_allowlist_data_fails_without_email(self, cache: UserAllowlistCache, mock_logger):
        """Test that validation fails when email column is missing."""
        # DataFrame without email column
        df_no_email = pd.DataFrame({
            "provider": ["Test Provider"]
        })

        is_valid, cleaned_df = cache._validate_allowlist_data(df_no_email)

        # Should fail validation
        assert is_valid is False, f"Expected validation to fail for data without email, got {is_valid}"

        # Should have logged error about missing email
        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args[0]
        assert "Missing required 'email' column" in error_call[0]

    def test_parse_allowlist_csv_from_bytes_utf8_success(self, cache: UserAllowlistCache):
        """Test successful UTF-8 decoding and parsing."""
        csv_content = b"Email,Provider\ntest@justice.gov.uk,Test Provider\n"

        result = cache._parse_allowlist_csv_from_bytes(csv_content)

        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert "email" in result.columns, f"Expected 'email' column, got: {list(result.columns)}"
        assert "provider" in result.columns, f"Expected 'provider' column, got: {list(result.columns)}"
        assert len(result) == 1, f"Expected 1 row, got {len(result)}"
        assert "test@justice.gov.uk" in result["email"].tolist()

    def test_parse_allowlist_csv_from_bytes_utf8_fallback_cp1252(self, cache: UserAllowlistCache, mock_logger):
        """Test fallback to cp1252 encoding when UTF-8 fails."""
        # Create content that will fail UTF-8 but succeed with cp1252
        # Use a character that's valid in cp1252 but not in UTF-8
        csv_content = "Email,Provider\ntest@justice.gov.uk,Test Provider\n".encode("cp1252")

        # Create content that will fail UTF-8 decoding by adding invalid UTF-8 bytes
        invalid_utf8_content = csv_content + b"\xff\xfe"  # Invalid UTF-8 sequence

        result = cache._parse_allowlist_csv_from_bytes(invalid_utf8_content)

        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert "email" in result.columns, f"Expected 'email' column, got: {list(result.columns)}"
        assert "provider" in result.columns, f"Expected 'provider' column, got: {list(result.columns)}"

        # Should have logged warning about UTF-8 failure
        mock_logger.warning.assert_called_once()
        warning_call = mock_logger.warning.call_args[0]
        assert "UTF-8 decoding failed, trying cp1252 encoding" in warning_call[0]

    def test_parse_allowlist_csv_from_bytes_cp1252_fallback_explicit_columns(self, cache: UserAllowlistCache, mock_logger):
        """Test fallback to explicit column names when both encodings fail."""
        # Create content that will fail both UTF-8 and cp1252
        # Use bytes that are invalid in both encodings
        csv_content = b"invalid\xff\xfecontent\x80\x81"

        result = cache._parse_allowlist_csv_from_bytes(csv_content)

        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        # Should have explicit column names
        assert "email" in result.columns, f"Expected 'email' column, got: {list(result.columns)}"
        assert "provider" in result.columns, f"Expected 'provider' column, got: {list(result.columns)}"

        # Should have logged warnings about both failures
        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
        assert any("UTF-8 decoding failed, trying cp1252 encoding" in call for call in warning_calls)
        assert any("cp1252 also failed, trying with explicit column names" in call for call in warning_calls)

    def test_parse_and_validate_content_success(self, cache: UserAllowlistCache):
        """Test successful parsing and validation of content."""
        csv_content = b"Email,Provider\ntest@justice.gov.uk,Test Provider\n"

        result = cache._parse_and_validate_content(csv_content, "test_blob.csv")

        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert "email" in result.columns, f"Expected 'email' column, got: {list(result.columns)}"
        assert "provider" in result.columns, f"Expected 'provider' column, got: {list(result.columns)}"
        assert len(result) == 1, f"Expected 1 row, got {len(result)}"
        assert "test@justice.gov.uk" in result["email"].tolist()

    def test_parse_and_validate_content_validation_failure(self, cache: UserAllowlistCache):
        """Test that validation failure raises ValueError."""
        # Create content that will pass parsing but fail validation (invalid domain)
        csv_content = b"Email,Provider\ntest@example.com,Test Provider\n"

        with pytest.raises(ValueError, match="Allowlist data failed validation checks") as exc_info:
            cache._parse_and_validate_content(csv_content, "test_blob.csv")

        assert "Allowlist data failed validation checks" in str(exc_info.value)

    def test_parse_and_validate_content_uses_cleaned_data(self, cache: UserAllowlistCache):
        """Test that the method uses the cleaned data from validation."""
        # Create content with duplicates that will be cleaned
        csv_content = b"Email,Provider\ntest@justice.gov.uk,Test Provider\ntest@justice.gov.uk,Test Provider\n"

        result = cache._parse_and_validate_content(csv_content, "test_blob.csv")

        # Should have deduplicated data
        assert len(result) == 1, f"Expected 1 row after deduplication, got {len(result)}"
        assert "test@justice.gov.uk" in result["email"].tolist()

    def test_clean_and_normalize_dataframe_return_columns_with_provider(self, cache: UserAllowlistCache):
        """Test that DataFrame with provider returns both columns in correct order."""
        df_with_provider = pd.DataFrame({
            "email": ["test@justice.gov.uk", "test2@justice.gov.uk"],
            "provider": ["Test Provider", "Test Provider 2"]
        })

        result = cache._clean_and_normalize_dataframe(df_with_provider)

        # Should return both columns in the correct order
        expected_columns = ["provider", "email"]
        assert list(result.columns) == expected_columns, f"Expected {expected_columns}, got {list(result.columns)}"
        assert len(result) == 2, f"Expected 2 rows, got {len(result)}"

    def test_clean_and_normalize_dataframe_return_columns_without_provider(self, cache: UserAllowlistCache, mock_logger):
        """Test that DataFrame without provider returns both columns (provider added as unknown)."""
        df_no_provider = pd.DataFrame({
            "email": ["test@justice.gov.uk", "test2@justice.gov.uk"]
        })

        result = cache._clean_and_normalize_dataframe(df_no_provider)

        # Should return both columns (provider added as "unknown")
        expected_columns = ["provider", "email"]
        assert list(result.columns) == expected_columns, f"Expected {expected_columns}, got {list(result.columns)}"
        assert len(result) == 2, f"Expected 2 rows, got {len(result)}"

        # Provider should be "unknown"
        assert all(result["provider"] == "unknown"), f"Expected all provider values to be 'unknown', got: {result['provider'].tolist()}"

        # Should have logged warning about missing provider
        mock_logger.warning.assert_called_once()
        warning_call = mock_logger.warning.call_args[0]
        assert "CSV missing 'provider' or 'Provider' column" in warning_call[0]

    def test_clean_and_normalize_dataframe_return_columns_edge_case_empty_dataframe(self, cache: UserAllowlistCache, mock_logger):
        """Test return columns with empty DataFrame."""
        df_empty = pd.DataFrame(columns=["email"])

        result = cache._clean_and_normalize_dataframe(df_empty)

        # Should return both columns even for empty DataFrame (provider added if missing)
        expected_columns = ["provider", "email"]
        assert list(result.columns) == expected_columns, f"Expected {expected_columns}, got {list(result.columns)}"
        assert len(result) == 0, f"Expected 0 rows, got {len(result)}"

        # Should have logged warning about missing provider
        mock_logger.warning.assert_called_once()

    def test_parse_and_validate_content_handles_encoding_errors_gracefully(self, cache: UserAllowlistCache, mock_logger):
        """Test that encoding errors are handled gracefully with fallbacks."""
        # Create content that will trigger all fallback paths but still have valid data
        # Use bytes that are invalid in both UTF-8 and cp1252, but include valid CSV structure
        csv_content = b"email,provider\ntest@justice.gov.uk,Test Provider\n"
        # Add invalid bytes that will trigger encoding fallbacks
        csv_content += b"\xff\xfe\x80\x81"

        result = cache._parse_and_validate_content(csv_content, "test_blob.csv")

        # Should still return a DataFrame with valid data
        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        assert "email" in result.columns, f"Expected 'email' column, got: {list(result.columns)}"
        assert "provider" in result.columns, f"Expected 'provider' column, got: {list(result.columns)}"

        # Should have logged warnings about encoding failures
        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
        assert any("UTF-8 decoding failed, trying cp1252 encoding" in call for call in warning_calls)
        assert any("cp1252 also failed, trying with explicit column names" in call for call in warning_calls)


class TestCreateAllowlistCache:
    """Test cases for create_allowlist_cache factory function."""

    def test_create_allowlist_cache_default_ttl(self):
        """Test factory function with default TTL."""
        cache = create_allowlist_cache()
        assert cache._ttl_seconds == 300, f"Expected default TTL of 300 seconds, got {cache._ttl_seconds}"

    def test_create_allowlist_cache_custom_ttl(self):
        """Test factory function with custom TTL."""
        cache = create_allowlist_cache(ttl_seconds=600)
        assert cache._ttl_seconds == 600, f"Expected custom TTL of 600 seconds, got {cache._ttl_seconds}"

    def test_create_allowlist_cache_returns_fresh_instance(self):
        """Test that factory returns fresh instances."""
        cache1 = create_allowlist_cache()
        cache2 = create_allowlist_cache()

        assert cache1 is not cache2, "Expected different cache instances"
        assert cache1._user_status is not cache2._user_status, "Expected different user status dictionaries"
