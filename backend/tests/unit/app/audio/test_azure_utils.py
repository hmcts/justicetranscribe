"""Test Azure Storage utilities for transcription upload to Azure Blob Storage."""

import pytest
from app.audio.azure_utils import _extract_account_name_from_connection_string

# Test connection strings
CONN_STR = "https;AccountName=<SOME_ACCOUNT_NAME>;AccountKey=<SOME_KEY>;EndpointSuffix=core.windows.net"
CONN_STR2 = "https;AccountName=<SOME_ACCOUNT_NAME>;AccountKey=<SOME_KEY>;EndpointSuffix=core.windows.net"
CONN_STR3 = "https;AccountName=;AccountKey=<SOME_KEY>;EndpointSuffix=core.windows.net"


class TestExtractAccountNameFromConnectionString:
    """Test cases for _extract_account_name_from_connection_string function."""

    def test_extract_account_name_from_valid_connection_string(self):
        """Test extracting account name from a valid connection string."""
        result = _extract_account_name_from_connection_string(CONN_STR)
        assert result == "<SOME_ACCOUNT_NAME>", f"Expected '<SOME_ACCOUNT_NAME>' but got '{result}' from connection string: {CONN_STR}"

    def test_extract_account_name_from_duplicate_connection_string(self):
        """Test extracting account name from second test connection string."""
        result = _extract_account_name_from_connection_string(CONN_STR2)
        assert result == "<SOME_ACCOUNT_NAME>", f"Expected '<SOME_ACCOUNT_NAME>' but got '{result}' from connection string: {CONN_STR2}"

    def test_extract_account_name_from_empty_account_name(self):
        """Test extracting account name when AccountName value is empty."""
        result = _extract_account_name_from_connection_string(CONN_STR3)
        assert result == "", f"Expected empty string but got '{result}' from connection string: {CONN_STR3}"

    def test_extract_account_name_real_azure_format(self):
        """Test with a realistic Azure Storage connection string format."""
        conn_str = "DefaultEndpointsProtocol=https;AccountName=myteststorage;AccountKey=abc123key;EndpointSuffix=core.windows.net"
        result = _extract_account_name_from_connection_string(conn_str)
        assert result == "myteststorage", f"Expected 'myteststorage' but got '{result}' from realistic Azure connection string: {conn_str}"

    def test_extract_account_name_different_order(self):
        """Test when AccountName appears in different position in connection string."""
        conn_str = "AccountKey=somekey;AccountName=testaccount;EndpointSuffix=core.windows.net"
        result = _extract_account_name_from_connection_string(conn_str)
        assert result == "testaccount", f"Expected 'testaccount' but got '{result}' when AccountName is in different position: {conn_str}"

    def test_extract_account_name_missing_account_name(self):
        """Test when AccountName is not present in connection string."""
        conn_str = "DefaultEndpointsProtocol=https;AccountKey=abc123key;EndpointSuffix=core.windows.net"
        result = _extract_account_name_from_connection_string(conn_str)
        assert result is None, f"Expected None but got '{result}' when AccountName is missing from: {conn_str}"

    def test_extract_account_name_empty_string(self):
        """Test with empty connection string."""
        result = _extract_account_name_from_connection_string("")
        assert result is None, f"Expected None but got '{result}' when connection string is empty"

    def test_extract_account_name_no_semicolon_separator(self):
        """Test with malformed connection string without semicolon separators."""
        conn_str = "AccountName=testaccount"
        result = _extract_account_name_from_connection_string(conn_str)
        assert result == "testaccount", f"Expected 'testaccount' but got '{result}' from connection string without semicolons: {conn_str}"

    def test_extract_account_name_no_equals_sign(self):
        """Test with malformed AccountName part without equals sign."""
        conn_str = "AccountName;AccountKey=somekey"
        result = _extract_account_name_from_connection_string(conn_str)
        assert result is None, f"Expected None but got '{result}' when AccountName has no equals sign: {conn_str}"

    def test_extract_account_name_multiple_equals_signs(self):
        """Test when AccountName value contains equals signs."""
        conn_str = "AccountName=test=account=name;AccountKey=somekey"
        result = _extract_account_name_from_connection_string(conn_str)
        assert result == "test=account=name", f"Expected 'test=account=name' but got '{result}' when AccountName value contains equals signs: {conn_str}"

    def test_extract_account_name_account_name_only_equals(self):
        """Test when AccountName= exists but no value after equals."""
        conn_str = "AccountName=;AccountKey=somekey"
        result = _extract_account_name_from_connection_string(conn_str)
        assert result == "", f"Expected empty string but got '{result}' when AccountName has no value after equals: {conn_str}"

    def test_extract_account_name_partial_match(self):
        """Test that partial matches like 'MyAccountName' don't match."""
        conn_str = "MyAccountName=shouldnotmatch;AccountName=correctname;AccountKey=key"
        result = _extract_account_name_from_connection_string(conn_str)
        assert result == "correctname", f"Expected 'correctname' but got '{result}' - partial matches should be ignored: {conn_str}"

    def test_extract_account_name_case_sensitive(self):
        """Test that the function is case sensitive for 'AccountName'."""
        conn_str = "accountname=lowercase;ACCOUNTNAME=uppercase;AccountKey=key"
        result = _extract_account_name_from_connection_string(conn_str)
        assert result is None, f"Expected None but got '{result}' - function should be case sensitive for 'AccountName': {conn_str}"

    def test_extract_account_name_whitespace_handling(self):
        """Test handling of whitespace around AccountName."""
        conn_str = " AccountName = spacedname ; AccountKey=key"
        result = _extract_account_name_from_connection_string(conn_str)
        # Function splits on ';' so ' AccountName ' won't match 'AccountName='
        assert result is None, f"Expected None but got '{result}' when AccountName has surrounding spaces: {conn_str}"
        
        # Test with exact match but spaces in value
        conn_str2 = "AccountName= spacedname ;AccountKey=key"
        result2 = _extract_account_name_from_connection_string(conn_str2)
        assert result2 == " spacedname ", f"Expected ' spacedname ' but got '{result2}' when AccountName value has spaces: {conn_str2}"

    @pytest.mark.parametrize("conn_str,expected", [
        ("AccountName=test", "test"),
        ("AccountName=", ""),
        ("SomethingElse=value", None),
        ("AccountName=value1;AccountName=value2", "value1"),  # First match wins
        ("", None),
    ])
    def test_extract_account_name_parametrized(self, conn_str, expected):
        """Parametrized tests for various connection string scenarios."""
        result = _extract_account_name_from_connection_string(conn_str)
        assert result == expected, f"Expected '{expected}' but got '{result}' from parametrized test with connection string: '{conn_str}'"

