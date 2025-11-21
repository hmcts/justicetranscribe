"""Integration tests for allowlist management system.

Tests the complete flow from CSV input through the add_users_to_allowlist.py script
to AllowlistManager validation, including edge cases.
"""

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from utils.allowlist import AllowlistManager


class TestAllowlistIntegration:
    """Integration tests for end-to-end allowlist functionality."""

    @pytest.fixture
    def temp_allowlist_dir(self, tmp_path: Path) -> Path:
        """Create a temporary directory for allowlist testing."""
        allowlist_dir = tmp_path / ".allowlist"
        allowlist_dir.mkdir(parents=True, exist_ok=True)
        return allowlist_dir

    @pytest.fixture
    def temp_allowlist_file(self, temp_allowlist_dir: Path) -> Path:
        """Create a temporary allowlist with initial users."""
        allowlist_path = temp_allowlist_dir / "allowlist.csv"
        initial_users = pd.DataFrame(
            {"email": ["existing1@justice.gov.uk", "existing2@justice.gov.uk", "existing3@justice.gov.uk"]}
        )
        initial_users.to_csv(allowlist_path, index=False)
        return allowlist_path

    def test_add_users_script_basic_functionality(self, temp_allowlist_file: Path, tmp_path: Path):
        """Test that the add_users script correctly adds new users."""
        # Create input CSV with new users
        input_csv = tmp_path / "input.csv"
        new_users = pd.DataFrame(
            {
                "email": [
                    "newuser1@justice.gov.uk",
                    "newuser2@justice.gov.uk",
                    "NEWUSER3@JUSTICE.GOV.UK",  # Test case normalization
                ]
            }
        )
        new_users.to_csv(input_csv, index=False)

        # Run the add_users script
        script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "allowlist" / "add_users_to_allowlist.py"
        result = subprocess.run(  # noqa: S603 - controlled test environment with trusted script path
            [sys.executable, str(script_path), "--file", str(input_csv), "--allowlist", str(temp_allowlist_file)],
            capture_output=True,
            text=True,
            env={"PYTHONPATH": str(Path(__file__).parent.parent.parent)},
            check=False,
        )

        assert result.returncode == 0
        assert "3 new user(s) added" in result.stdout

        # Verify users were added
        allowlist_df = pd.read_csv(temp_allowlist_file)
        assert len(allowlist_df) == 6  # 3 existing + 3 new
        assert "newuser1@justice.gov.uk" in allowlist_df["email"].to_numpy()
        assert "newuser2@justice.gov.uk" in allowlist_df["email"].to_numpy()
        assert "newuser3@justice.gov.uk" in allowlist_df["email"].to_numpy()  # Should be lowercase

    def test_add_users_filters_duplicates(self, temp_allowlist_file: Path, tmp_path: Path):
        """Test that duplicate entries are filtered out."""
        # Create input CSV with duplicates
        input_csv = tmp_path / "input_duplicates.csv"
        users_with_dupes = pd.DataFrame(
            {
                "email": [
                    "newuser@justice.gov.uk",
                    "NEWUSER@JUSTICE.GOV.UK",  # Duplicate (different case)
                    "newuser@justice.gov.uk",  # Duplicate (exact)
                    "existing1@justice.gov.uk",  # Already in allowlist
                    "EXISTING2@JUSTICE.GOV.UK",  # Already in allowlist (different case)
                    "unique@justice.gov.uk",  # Only unique new user
                ]
            }
        )
        users_with_dupes.to_csv(input_csv, index=False)

        # Run the add_users script
        script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "allowlist" / "add_users_to_allowlist.py"
        result = subprocess.run(  # noqa: S603 - controlled test environment with trusted script path
            [sys.executable, str(script_path), "--file", str(input_csv), "--allowlist", str(temp_allowlist_file)],
            capture_output=True,
            text=True,
            env={"PYTHONPATH": str(Path(__file__).parent.parent.parent)},
            check=False,
        )

        assert result.returncode == 0
        # Should only add 2 new users (newuser and unique), not the duplicates or existing ones
        assert "2 new user(s) added" in result.stdout
        assert "newuser@justice.gov.uk" in result.stdout
        assert "unique@justice.gov.uk" in result.stdout

        # Verify final allowlist has no duplicates
        allowlist_df = pd.read_csv(temp_allowlist_file)
        assert len(allowlist_df) == 5  # 3 existing + 2 new (duplicates filtered)

        # Check for duplicates in the final allowlist
        lowercase_emails = allowlist_df["email"].str.lower()
        assert len(lowercase_emails) == len(lowercase_emails.unique())

    def test_add_users_handles_apostrophes(self, temp_allowlist_file: Path, tmp_path: Path):
        """Test that emails with apostrophes are handled correctly."""
        # Create input CSV with apostrophes (real edge case that has caused issues)
        input_csv = tmp_path / "input_apostrophes.csv"
        users_with_apostrophes = pd.DataFrame(
            {
                "email": [
                    "o'connor@justice.gov.uk",
                    "mc'donald@justice.gov.uk",
                    "o'brien@justice.gov.uk",
                    "d'angelo@justice.gov.uk",
                ]
            }
        )
        users_with_apostrophes.to_csv(input_csv, index=False)

        # Run the add_users script
        script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "allowlist" / "add_users_to_allowlist.py"
        result = subprocess.run(  # noqa: S603 - controlled test environment with trusted script path
            [sys.executable, str(script_path), "--file", str(input_csv), "--allowlist", str(temp_allowlist_file)],
            capture_output=True,
            text=True,
            env={"PYTHONPATH": str(Path(__file__).parent.parent.parent)},
            check=False,
        )

        assert result.returncode == 0
        assert "4 new user(s) added" in result.stdout

        # Verify users with apostrophes were added
        allowlist_df = pd.read_csv(temp_allowlist_file)
        assert "o'connor@justice.gov.uk" in allowlist_df["email"].to_numpy()
        assert "mc'donald@justice.gov.uk" in allowlist_df["email"].to_numpy()
        assert "o'brien@justice.gov.uk" in allowlist_df["email"].to_numpy()
        assert "d'angelo@justice.gov.uk" in allowlist_df["email"].to_numpy()

        # Verify AllowlistManager can check these emails
        manager = AllowlistManager(temp_allowlist_file)
        assert manager.is_user_allowlisted("o'connor@justice.gov.uk") is True
        assert manager.is_user_allowlisted("O'Connor@Justice.Gov.Uk") is True  # Case insensitive
        assert manager.is_user_allowlisted("mc'donald@justice.gov.uk") is True
        assert manager.is_user_allowlisted("notinlist@justice.gov.uk") is False

    def test_add_users_rejects_invalid_domains(self, temp_allowlist_file: Path, tmp_path: Path):
        """Test that emails with wrong domains are rejected."""
        # Create input CSV with mixed valid and invalid domains
        input_csv = tmp_path / "input_mixed_domains.csv"
        mixed_domains = pd.DataFrame(
            {
                "email": [
                    "valid@justice.gov.uk",
                    "invalid@gmail.com",
                    "wrong@example.com",
                    "nope@justice.com",
                    "another-valid@justice.gov.uk",
                ]
            }
        )
        mixed_domains.to_csv(input_csv, index=False)

        # Run the add_users script
        script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "allowlist" / "add_users_to_allowlist.py"
        result = subprocess.run(  # noqa: S603 - controlled test environment with trusted script path
            [sys.executable, str(script_path), "--file", str(input_csv), "--allowlist", str(temp_allowlist_file)],
            capture_output=True,
            text=True,
            env={"PYTHONPATH": str(Path(__file__).parent.parent.parent)},
            check=False,
        )

        assert result.returncode == 0
        # Only 2 valid emails should be added
        assert "2 new user(s) added" in result.stdout
        assert "3 rejected" in result.stdout
        assert "must end with @justice.gov.uk" in result.stdout

        # Verify only valid emails were added
        allowlist_df = pd.read_csv(temp_allowlist_file)
        assert "valid@justice.gov.uk" in allowlist_df["email"].to_numpy()
        assert "another-valid@justice.gov.uk" in allowlist_df["email"].to_numpy()
        assert "invalid@gmail.com" not in allowlist_df["email"].to_numpy()
        assert "wrong@example.com" not in allowlist_df["email"].to_numpy()

    def test_end_to_end_with_allowlist_manager(self, temp_allowlist_file: Path, tmp_path: Path):
        """Test complete flow: add users via script, then validate via AllowlistManager."""
        # Create input CSV
        input_csv = tmp_path / "input_e2e.csv"
        test_users = pd.DataFrame(
            {
                "email": [
                    "alice@justice.gov.uk",
                    "bob@justice.gov.uk",
                    "charlie@justice.gov.uk",
                    "alice@justice.gov.uk",  # Duplicate
                    "invalid@gmail.com",  # Should be rejected
                ]
            }
        )
        test_users.to_csv(input_csv, index=False)

        # Step 1: Add users via script
        script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "allowlist" / "add_users_to_allowlist.py"
        result = subprocess.run(  # noqa: S603 - controlled test environment with trusted script path
            [sys.executable, str(script_path), "--file", str(input_csv), "--allowlist", str(temp_allowlist_file)],
            capture_output=True,
            text=True,
            env={"PYTHONPATH": str(Path(__file__).parent.parent.parent)},
            check=False,
        )

        assert result.returncode == 0
        assert "3 new user(s) added" in result.stdout  # 3 valid, deduplicated

        # Step 2: Verify with AllowlistManager
        manager = AllowlistManager(temp_allowlist_file)

        # Valid users should be allowed
        assert manager.is_user_allowlisted("alice@justice.gov.uk") is True
        assert manager.is_user_allowlisted("ALICE@JUSTICE.GOV.UK") is True  # Case insensitive
        assert manager.is_user_allowlisted("bob@justice.gov.uk") is True
        assert manager.is_user_allowlisted("charlie@justice.gov.uk") is True

        # Invalid/rejected users should not be allowed
        assert manager.is_user_allowlisted("invalid@gmail.com") is False
        assert manager.is_user_allowlisted("notadded@justice.gov.uk") is False

        # Existing users should still be allowed
        assert manager.is_user_allowlisted("existing1@justice.gov.uk") is True
        assert manager.is_user_allowlisted("existing2@justice.gov.uk") is True

    def test_allowlist_manager_handles_empty_allowlist(self, tmp_path: Path):
        """Test that empty allowlist fails open (returns True)."""
        empty_allowlist = tmp_path / "empty_allowlist.csv"
        pd.DataFrame({"email": []}).to_csv(empty_allowlist, index=False)

        manager = AllowlistManager(empty_allowlist)
        # Should fail-open and return True for any email
        assert manager.is_user_allowlisted("anyone@justice.gov.uk") is True

    def test_allowlist_manager_handles_missing_file(self, tmp_path: Path):
        """Test that missing allowlist file fails open (returns True)."""
        nonexistent = tmp_path / "nonexistent.csv"

        manager = AllowlistManager(nonexistent)
        # Should fail-open and return True for any email
        assert manager.is_user_allowlisted("anyone@justice.gov.uk") is True

    def test_complex_edge_cases_combined(self, temp_allowlist_file: Path, tmp_path: Path):
        """Test multiple edge cases in a single batch."""
        # Create input with various edge cases
        input_csv = tmp_path / "input_complex.csv"
        complex_data = pd.DataFrame(
            {
                "email": [
                    "  whitespace@justice.gov.uk  ",  # Extra whitespace
                    "UPPERCASE@JUSTICE.GOV.UK",  # Uppercase
                    "MiXeD.CaSe@JuStIcE.GoV.uK",  # Mixed case
                    "o'reilly@justice.gov.uk",  # Apostrophe
                    "existing1@justice.gov.uk",  # Already exists
                    "EXISTING2@JUSTICE.GOV.UK",  # Already exists (different case)
                    "duplicate@justice.gov.uk",  # Will be duplicated below
                    "duplicate@justice.gov.uk",  # Duplicate
                    "DUPLICATE@JUSTICE.GOV.UK",  # Duplicate (different case)
                    "invalid@yahoo.com",  # Wrong domain
                    "no-at-symbol",  # Invalid format
                    "",  # Empty
                    "valid-new@justice.gov.uk",  # Valid new user
                ]
            }
        )
        complex_data.to_csv(input_csv, index=False)

        # Run the add_users script
        script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "allowlist" / "add_users_to_allowlist.py"
        result = subprocess.run(  # noqa: S603 - controlled test environment with trusted script path
            [sys.executable, str(script_path), "--file", str(input_csv), "--allowlist", str(temp_allowlist_file)],
            capture_output=True,
            text=True,
            env={"PYTHONPATH": str(Path(__file__).parent.parent.parent)},
            check=False,
        )

        assert result.returncode == 0

        # Verify the allowlist
        allowlist_df = pd.read_csv(temp_allowlist_file)
        emails = set(allowlist_df["email"].str.lower())

        # Should include new valid users (normalized)
        assert "whitespace@justice.gov.uk" in emails
        assert "uppercase@justice.gov.uk" in emails
        assert "mixed.case@justice.gov.uk" in emails
        assert "o'reilly@justice.gov.uk" in emails
        assert "duplicate@justice.gov.uk" in emails
        assert "valid-new@justice.gov.uk" in emails

        # Should NOT include invalid entries
        assert "invalid@yahoo.com" not in emails

        # Should not have duplicates
        email_counts = allowlist_df["email"].str.lower().value_counts()
        assert all(count == 1 for count in email_counts.to_numpy())

        # Verify with AllowlistManager
        manager = AllowlistManager(temp_allowlist_file)
        assert manager.is_user_allowlisted("WhiteSpace@Justice.Gov.Uk") is True
        assert manager.is_user_allowlisted("O'REILLY@JUSTICE.GOV.UK") is True
        assert manager.is_user_allowlisted("invalid@yahoo.com") is False
