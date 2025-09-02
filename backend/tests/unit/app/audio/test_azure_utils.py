"""Test Azure Storage utilities for transcription upload to Azure Blob Storage."""

import pytest
from app.audio.azure_utils import _extract_account_name_from_connection_string


@pytest.fixture()
def valid_connection_string():
    """Valid Azure Storage connection string for testing."""
    return "https;AccountName=<SOME_ACCOUNT_NAME>;AccountKey=<SOME_KEY>;EndpointSuffix=core.windows.net"


@pytest.fixture()
def empty_account_name_connection_string():
    """Connection string with empty AccountName value."""
    return "https;AccountName=;AccountKey=<SOME_KEY>;EndpointSuffix=core.windows.net"


@pytest.fixture()
def missing_account_name_connection_string():
    """Connection string missing AccountName parameter."""
    return "DefaultEndpointsProtocol=https;AccountKey=abc123key;EndpointSuffix=core.windows.net"


@pytest.fixture()
def malformed_account_name_connection_string():
    """Connection string with malformed AccountName (no equals sign)."""
    return "AccountName;AccountKey=somekey"


@pytest.fixture()
def case_sensitive_connection_string():
    """Connection string with incorrect case for AccountName."""
    return "accountname=lowercase;ACCOUNTNAME=uppercase;AccountKey=key"


@pytest.fixture()
def whitespace_connection_string():
    """Connection string with whitespace issues."""
    return "AccountName= spacedname ;AccountKey=key"


@pytest.fixture()
def multiple_equals_connection_string():
    """Connection string with AccountName value containing equals signs."""
    return "AccountName=test=account=name;AccountKey=somekey"


@pytest.fixture()
def whitespace_only_connection_string():
    """Connection string that is only whitespace."""
    return "   \t\n  "


@pytest.fixture()
def multiple_account_name_connection_string():
    """Connection string with multiple AccountName parameters."""
    return "AccountName=first;AccountName=second;AccountKey=somekey"


class TestExtractAccountNameFromConnectionString:
    """Test cases for _extract_account_name_from_connection_string."""

    def test_extract_account_name_from_valid_connection_string(self, valid_connection_string):
        """Test extracting account name from a valid connection string."""
        result = _extract_account_name_from_connection_string(valid_connection_string)
        assert result == "<SOME_ACCOUNT_NAME>", f"Expected '<SOME_ACCOUNT_NAME>' but got '{result}' from connection string: {valid_connection_string}"

    def test_extract_account_name_from_empty_account_name(self, empty_account_name_connection_string):
        """Test extracting account name when AccountName value is empty."""
        with pytest.raises(ValueError, match="AccountName parameter cannot be empty"):
            _extract_account_name_from_connection_string(empty_account_name_connection_string)

    def test_extract_account_name_missing_account_name(self, missing_account_name_connection_string):
        """Test when AccountName is not present in connection string."""
        with pytest.raises(ValueError, match="AccountName parameter not found in connection string"):
            _extract_account_name_from_connection_string(missing_account_name_connection_string)

    def test_extract_account_name_empty_string(self):
        """Test with empty connection string."""
        with pytest.raises(ValueError, match="Connection string cannot be empty"):
            _extract_account_name_from_connection_string("")

    def test_extract_account_name_no_semicolon_separator(self):
        """Test with malformed connection string without semicolon separators."""
        conn_str = "AccountName=testaccount"
        result = _extract_account_name_from_connection_string(conn_str)
        assert result == "testaccount", f"Expected 'testaccount' but got '{result}' from connection string without semicolons: {conn_str}"

    def test_extract_account_name_no_equals_sign(self, malformed_account_name_connection_string):
        """Test with malformed AccountName part without equals sign."""
        with pytest.raises(ValueError, match="Malformed AccountName parameter: missing equals sign"):
            _extract_account_name_from_connection_string(malformed_account_name_connection_string)

    def test_extract_account_name_multiple_equals_signs(self, multiple_equals_connection_string):
        """Test when AccountName value contains equals signs."""
        result = _extract_account_name_from_connection_string(multiple_equals_connection_string)
        assert result == "test=account=name", f"Expected 'test=account=name' but got '{result}' when AccountName value contains equals signs: {multiple_equals_connection_string}"

    def test_extract_account_name_case_sensitive(self, case_sensitive_connection_string):
        """Test that the function is case sensitive for 'AccountName'."""
        with pytest.raises(ValueError, match=r"AccountName parameter must use exact case 'AccountName=' \(found: 'accountname='\)"):
            _extract_account_name_from_connection_string(case_sensitive_connection_string)

    def test_extract_account_name_whitespace_handling(self, whitespace_connection_string):
        """Test handling of whitespace around AccountName."""
        # Test with malformed AccountName (spaces around parameter name)
        conn_str = " AccountName = spacedname ; AccountKey=key"
        # Function splits on ';' so ' AccountName ' won't match 'AccountName='
        with pytest.raises(ValueError, match="AccountName parameter not found in connection string"):
            _extract_account_name_from_connection_string(conn_str)
        
        # Test with exact match but spaces in value - whitespace should be stripped
        result = _extract_account_name_from_connection_string(whitespace_connection_string)
        assert result == "spacedname", f"Expected 'spacedname' but got '{result}' when AccountName value has spaces: {whitespace_connection_string}"

    def test_extract_account_name_whitespace_only_string(self, whitespace_only_connection_string):
        """Test with connection string that is only whitespace."""
        with pytest.raises(ValueError, match="Connection string cannot be whitespace only"):
            _extract_account_name_from_connection_string(whitespace_only_connection_string)

    def test_extract_account_name_multiple_account_names(self, multiple_account_name_connection_string):
        """Test with connection string containing multiple AccountName parameters."""
        with pytest.raises(ValueError, match="Multiple AccountName parameters found in connection string"):
            _extract_account_name_from_connection_string(multiple_account_name_connection_string)
