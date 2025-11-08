"""Unit tests for simplified allowlist functionality."""

from pathlib import Path

import pandas as pd
import pytest

from utils.allowlist import AllowlistManager, get_allowlist_manager


class TestAllowlistManager:
    """Test cases for AllowlistManager class."""

    @pytest.fixture
    def temp_csv_file(self, tmp_path: Path) -> Path:
        """Create a temporary CSV file with test data."""
        csv_path = tmp_path / "test_allowlist.csv"
        test_data = pd.DataFrame({
            "email": ["test1@example.com", "test2@example.com", "TEST3@EXAMPLE.COM"],
            "provider": ["Provider1", "Provider2", "Provider3"]
        })
        test_data.to_csv(csv_path, index=False)
        return csv_path

    @pytest.fixture
    def manager(self, temp_csv_file: Path) -> AllowlistManager:
        """Create a fresh AllowlistManager instance for each test."""
        return AllowlistManager(temp_csv_file)

    def test_initialization_with_default_path(self):
        """Test manager initializes with default path."""
        manager = AllowlistManager()
        assert manager.csv_path is not None
        assert manager._allowed_emails is None

    def test_initialization_with_custom_path(self, temp_csv_file: Path):
        """Test manager initializes with custom path."""
        manager = AllowlistManager(temp_csv_file)
        assert manager.csv_path == temp_csv_file
        assert manager._allowed_emails is None

    def test_load_allowlist_success(self, manager: AllowlistManager):
        """Test successful allowlist loading."""
        emails = manager._load_allowlist()
        assert isinstance(emails, set)
        assert len(emails) == 3
        assert "test1@example.com" in emails
        assert "test2@example.com" in emails
        assert "test3@example.com" in emails  # Should be lowercased

    def test_load_allowlist_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        manager = AllowlistManager("/nonexistent/path.csv")
        with pytest.raises(FileNotFoundError, match="Allowlist file not found"):
            manager._load_allowlist()

    def test_load_allowlist_missing_email_column(self, tmp_path: Path):
        """Test that ValueError is raised for missing email column."""
        csv_path = tmp_path / "invalid.csv"
        invalid_data = pd.DataFrame({"name": ["John", "Jane"]})
        invalid_data.to_csv(csv_path, index=False)

        manager = AllowlistManager(csv_path)
        with pytest.raises(ValueError, match="CSV must contain 'email' column"):
            manager._load_allowlist()

    def test_load_allowlist_no_valid_emails(self, tmp_path: Path):
        """Test that ValueError is raised when no valid emails found."""
        csv_path = tmp_path / "empty_emails.csv"
        empty_data = pd.DataFrame({"email": ["", "nan", "   "]})
        empty_data.to_csv(csv_path, index=False)

        manager = AllowlistManager(csv_path)
        with pytest.raises(ValueError, match="No valid emails found"):
            manager._load_allowlist()

    def test_load_allowlist_normalizes_emails(self, tmp_path: Path):
        """Test that emails are normalized to lowercase."""
        csv_path = tmp_path / "uppercase.csv"
        emails_data = pd.DataFrame({"email": ["TEST@EXAMPLE.COM", " Another@Example.com ", "lower@example.com"]})
        emails_data.to_csv(csv_path, index=False)

        manager = AllowlistManager(csv_path)
        emails = manager._load_allowlist()

        assert "test@example.com" in emails
        assert "another@example.com" in emails
        assert "lower@example.com" in emails
        assert len(emails) == 3

    def test_load_allowlist_removes_duplicates(self, tmp_path: Path):
        """Test that duplicate emails are removed."""
        csv_path = tmp_path / "duplicates.csv"
        duplicate_data = pd.DataFrame({
            "email": ["test@example.com", "TEST@EXAMPLE.COM", "test@example.com", "other@example.com"]
        })
        duplicate_data.to_csv(csv_path, index=False)

        manager = AllowlistManager(csv_path)
        emails = manager._load_allowlist()

        assert len(emails) == 2  # Only unique emails
        assert "test@example.com" in emails
        assert "other@example.com" in emails

    def test_load_allowlist_filters_invalid_emails(self, tmp_path: Path):
        """Test that invalid emails are filtered out."""
        csv_path = tmp_path / "invalid_emails.csv"
        invalid_emails_data = pd.DataFrame({
            "email": ["valid@example.com", "invalid-no-at", "", "another@valid.com"]
        })
        invalid_emails_data.to_csv(csv_path, index=False)

        manager = AllowlistManager(csv_path)
        emails = manager._load_allowlist()

        assert len(emails) == 2
        assert "valid@example.com" in emails
        assert "another@valid.com" in emails

    def test_is_user_allowlisted_none_email(self, manager: AllowlistManager):
        """Test allowlist check with None email."""
        assert manager.is_user_allowlisted(None) is False

    def test_is_user_allowlisted_empty_email(self, manager: AllowlistManager):
        """Test allowlist check with empty email."""
        assert manager.is_user_allowlisted("") is False

    def test_is_user_allowlisted_valid_email(self, manager: AllowlistManager):
        """Test allowlist check with valid allowlisted email."""
        assert manager.is_user_allowlisted("test1@example.com") is True
        assert manager.is_user_allowlisted("test2@example.com") is True

    def test_is_user_allowlisted_invalid_email(self, manager: AllowlistManager):
        """Test allowlist check with non-allowlisted email."""
        assert manager.is_user_allowlisted("notinlist@example.com") is False

    def test_is_user_allowlisted_case_insensitive(self, manager: AllowlistManager):
        """Test that email checking is case-insensitive."""
        assert manager.is_user_allowlisted("TEST1@EXAMPLE.COM") is True
        assert manager.is_user_allowlisted("Test2@Example.Com") is True

    def test_is_user_allowlisted_whitespace_handling(self, manager: AllowlistManager):
        """Test that whitespace in emails is handled."""
        assert manager.is_user_allowlisted("  test1@example.com  ") is True

    def test_is_user_allowlisted_loads_once(self, manager: AllowlistManager):
        """Test that allowlist is only loaded once."""
        # First check loads the data
        manager.is_user_allowlisted("test1@example.com")
        assert manager._allowed_emails is not None
        first_load = manager._allowed_emails

        # Second check should use cached data
        manager.is_user_allowlisted("test2@example.com")
        assert manager._allowed_emails is first_load

    def test_is_user_allowlisted_handles_load_failure(self):
        """Test that load failures return False."""
        manager = AllowlistManager("/nonexistent/path.csv")
        assert manager.is_user_allowlisted("test@example.com") is False

    def test_reload_clears_cache(self, manager: AllowlistManager):
        """Test that reload clears the cached data."""
        # Load the data
        manager.is_user_allowlisted("test1@example.com")
        assert manager._allowed_emails is not None

        # Reload should clear the cache
        manager.reload()
        assert manager._allowed_emails is None

    def test_reload_reloads_on_next_check(self, manager: AllowlistManager, temp_csv_file: Path):
        """Test that data is reloaded after reload() call."""
        # Load the data
        manager.is_user_allowlisted("test1@example.com")

        # Modify the CSV file
        new_data = pd.DataFrame({"email": ["newuser@example.com"]})
        new_data.to_csv(temp_csv_file, index=False)

        # Reload and check
        manager.reload()
        assert manager.is_user_allowlisted("newuser@example.com") is True
        assert manager.is_user_allowlisted("test1@example.com") is False


class TestGetAllowlistManager:
    """Test cases for get_allowlist_manager singleton function."""

    def test_returns_singleton_instance(self):
        """Test that get_allowlist_manager returns the same instance."""
        manager1 = get_allowlist_manager()
        manager2 = get_allowlist_manager()
        assert manager1 is manager2

    def test_singleton_with_custom_path(self, tmp_path: Path):
        """Test that singleton uses path from first creation."""
        # Reset the global singleton for this test
        import utils.allowlist
        utils.allowlist._global_allowlist = None

        csv_path = tmp_path / "test.csv"
        test_data = pd.DataFrame({"email": ["test@example.com"]})
        test_data.to_csv(csv_path, index=False)

        manager1 = get_allowlist_manager(csv_path)
        manager2 = get_allowlist_manager()  # Should use same path

        assert manager1 is manager2
        assert manager1.csv_path == csv_path

        # Clean up
        utils.allowlist._global_allowlist = None
