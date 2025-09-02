"""Test Azure Storage utilities for transcription upload to Azure Blob Storage."""

import pytest
from azure.core.exceptions import ClientAuthenticationError

from app.audio.azure_utils import (
    _extract_account_key_from_connection_string,
    _extract_account_name_from_connection_string,
    _validate_azure_account_key,
    validate_azure_storage_config,
)


@pytest.fixture
def valid_connection_string():
    """Valid Azure Storage connection string for testing."""
    return "https;AccountName=<SOME_ACCOUNT_NAME>;AccountKey=<SOME_KEY>;EndpointSuffix=core.windows.net"


@pytest.fixture
def empty_account_name_connection_string():
    """Connection string with empty AccountName value."""
    return "https;AccountName=;AccountKey=<SOME_KEY>;EndpointSuffix=core.windows.net"


@pytest.fixture
def missing_account_name_connection_string():
    """Connection string missing AccountName parameter."""
    return "DefaultEndpointsProtocol=https;AccountKey=abc123key;EndpointSuffix=core.windows.net"


@pytest.fixture
def malformed_account_name_connection_string():
    """Connection string with malformed AccountName (no equals sign)."""
    return "AccountName;AccountKey=somekey"


@pytest.fixture
def case_sensitive_connection_string():
    """Connection string with incorrect case for AccountName."""
    return "accountname=lowercase;ACCOUNTNAME=uppercase;AccountKey=key"


@pytest.fixture
def whitespace_connection_string():
    """Connection string with whitespace issues."""
    return "AccountName= spacedname ;AccountKey=key"


@pytest.fixture
def multiple_equals_connection_string():
    """Connection string with AccountName value containing equals signs."""
    return "AccountName=test=account=name;AccountKey=somekey"


@pytest.fixture
def whitespace_only_connection_string():
    """Connection string that is only whitespace."""
    return "   \t\n  "


@pytest.fixture
def multiple_account_name_connection_string():
    """Connection string with multiple AccountName parameters."""
    return "AccountName=first;AccountName=second;AccountKey=somekey"


@pytest.fixture
def valid_account_key_connection_string():
    """Valid Azure Storage connection string for AccountKey testing."""
    return "AccountName=testaccount;AccountKey=<SOME_ACCOUNT_KEY>;EndpointSuffix=core.windows.net"


@pytest.fixture
def empty_account_key_connection_string():
    """Connection string with empty AccountKey value."""
    return "AccountName=testaccount;AccountKey=;EndpointSuffix=core.windows.net"


@pytest.fixture
def missing_account_key_connection_string():
    """Connection string missing AccountKey parameter."""
    return "DefaultEndpointsProtocol=https;AccountName=testaccount;EndpointSuffix=core.windows.net"


@pytest.fixture
def malformed_account_key_connection_string():
    """Connection string with malformed AccountKey (no equals sign)."""
    return "AccountName=testaccount;AccountKey;EndpointSuffix=core.windows.net"


@pytest.fixture
def case_sensitive_account_key_connection_string():
    """Connection string with incorrect case for AccountKey."""
    return "AccountName=testaccount;accountkey=lowercase;ACCOUNTKEY=uppercase"


@pytest.fixture
def whitespace_account_key_connection_string():
    """Connection string with whitespace in AccountKey value."""
    return "AccountName=testaccount;AccountKey= spacedkey ;EndpointSuffix=core.windows.net"


@pytest.fixture
def multiple_equals_account_key_connection_string():
    """Connection string with AccountKey value containing equals signs."""
    return "AccountName=testaccount;AccountKey=key=with=equals;EndpointSuffix=core.windows.net"


@pytest.fixture
def multiple_account_key_connection_string():
    """Connection string with multiple AccountKey parameters."""
    return "AccountName=testaccount;AccountKey=first;AccountKey=second;EndpointSuffix=core.windows.net"


@pytest.fixture
def complete_valid_connection_string():
    """Complete valid Azure Storage connection string for validation testing."""
    return (
        "DefaultEndpointsProtocol=https;AccountName=validaccount;AccountKey=validkey123;EndpointSuffix=core.windows.net"
    )


@pytest.fixture
def mock_blob_service_client(mocker):
    """Mock BlobServiceClient for testing Azure operations."""
    mock_client = mocker.MagicMock()
    mocker.patch("app.audio.azure_utils.BlobServiceClient", return_value=mock_client)
    return mock_client


class TestExtractAccountNameFromConnectionString:
    """Test cases for _extract_account_name_from_connection_string."""

    def test_extract_account_name_from_valid_connection_string(self, valid_connection_string):
        """Test extracting account name from a valid connection string."""
        result = _extract_account_name_from_connection_string(valid_connection_string)
        assert (
            result == "<SOME_ACCOUNT_NAME>"
        ), f"Expected '<SOME_ACCOUNT_NAME>' but got '{result}' from connection string: {valid_connection_string}"

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
        assert (
            result == "testaccount"
        ), f"Expected 'testaccount' but got '{result}' from connection string without semicolons: {conn_str}"

    def test_extract_account_name_no_equals_sign(self, malformed_account_name_connection_string):
        """Test with malformed AccountName part without equals sign."""
        with pytest.raises(ValueError, match="Malformed AccountName parameter: missing equals sign"):
            _extract_account_name_from_connection_string(malformed_account_name_connection_string)

    def test_extract_account_name_multiple_equals_signs(self, multiple_equals_connection_string):
        """Test when AccountName value contains equals signs."""
        result = _extract_account_name_from_connection_string(multiple_equals_connection_string)
        assert (
            result == "test=account=name"
        ), f"Expected 'test=account=name' but got '{result}' when AccountName value contains equals signs: {multiple_equals_connection_string}"

    def test_extract_account_name_case_sensitive(self, case_sensitive_connection_string):
        """Test that the function is case sensitive for 'AccountName'."""
        with pytest.raises(
            ValueError, match=r"AccountName parameter must use exact case 'AccountName=' \(found: 'accountname='\)"
        ):
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
        assert (
            result == "spacedname"
        ), f"Expected 'spacedname' but got '{result}' when AccountName value has spaces: {whitespace_connection_string}"

    def test_extract_account_name_whitespace_only_string(self, whitespace_only_connection_string):
        """Test with connection string that is only whitespace."""
        with pytest.raises(ValueError, match="Connection string cannot be whitespace only"):
            _extract_account_name_from_connection_string(whitespace_only_connection_string)

    def test_extract_account_name_multiple_account_names(self, multiple_account_name_connection_string):
        """Test with connection string containing multiple AccountName parameters."""
        with pytest.raises(ValueError, match="Multiple AccountName parameters found in connection string"):
            _extract_account_name_from_connection_string(multiple_account_name_connection_string)


class TestExtractAccountKeyFromConnectionString:
    """Test cases for _extract_account_key_from_connection_string."""

    def test_extract_account_key_from_valid_connection_string(self, valid_account_key_connection_string):
        """Test extracting account key from a valid connection string."""
        result = _extract_account_key_from_connection_string(valid_account_key_connection_string)
        assert (
            result == "<SOME_ACCOUNT_KEY>"
        ), f"Expected '<SOME_ACCOUNT_KEY>' but got '{result}' from connection string: {valid_account_key_connection_string}"

    def test_extract_account_key_from_empty_account_key(self, empty_account_key_connection_string):
        """Test extracting account key when AccountKey value is empty."""
        with pytest.raises(ValueError, match="AccountKey parameter cannot be empty"):
            _extract_account_key_from_connection_string(empty_account_key_connection_string)

    def test_extract_account_key_missing_account_key(self, missing_account_key_connection_string):
        """Test when AccountKey is not present in connection string."""
        with pytest.raises(ValueError, match="AccountKey parameter not found in connection string"):
            _extract_account_key_from_connection_string(missing_account_key_connection_string)

    def test_extract_account_key_empty_string(self):
        """Test with empty connection string."""
        with pytest.raises(ValueError, match="Connection string cannot be empty"):
            _extract_account_key_from_connection_string("")

    def test_extract_account_key_no_semicolon_separator(self):
        """Test with malformed connection string without semicolon separators."""
        conn_str = "AccountKey=testkey"
        result = _extract_account_key_from_connection_string(conn_str)
        assert (
            result == "testkey"
        ), f"Expected 'testkey' but got '{result}' from connection string without semicolons: {conn_str}"

    def test_extract_account_key_no_equals_sign(self, malformed_account_key_connection_string):
        """Test with malformed AccountKey part without equals sign."""
        with pytest.raises(ValueError, match="Malformed AccountKey parameter: missing equals sign"):
            _extract_account_key_from_connection_string(malformed_account_key_connection_string)

    def test_extract_account_key_multiple_equals_signs(self, multiple_equals_account_key_connection_string):
        """Test when AccountKey value contains equals signs."""
        result = _extract_account_key_from_connection_string(multiple_equals_account_key_connection_string)
        assert (
            result == "key=with=equals"
        ), f"Expected 'key=with=equals' but got '{result}' when AccountKey value contains equals signs: {multiple_equals_account_key_connection_string}"

    def test_extract_account_key_case_sensitive(self, case_sensitive_account_key_connection_string):
        """Test that the function is case sensitive for 'AccountKey'."""
        with pytest.raises(
            ValueError, match=r"AccountKey parameter must use exact case 'AccountKey=' \(found: 'accountkey='\)"
        ):
            _extract_account_key_from_connection_string(case_sensitive_account_key_connection_string)

    def test_extract_account_key_whitespace_handling(self, whitespace_account_key_connection_string):
        """Test handling of whitespace around AccountKey."""
        # Test with malformed AccountKey (spaces around parameter name)
        conn_str = " AccountKey = spacedkey ; AccountName=test"
        # Function splits on ';' so ' AccountKey ' won't match 'AccountKey='
        with pytest.raises(ValueError, match="AccountKey parameter not found in connection string"):
            _extract_account_key_from_connection_string(conn_str)

        # Test with exact match but spaces in value - whitespace should be stripped
        result = _extract_account_key_from_connection_string(whitespace_account_key_connection_string)
        assert (
            result == "spacedkey"
        ), f"Expected 'spacedkey' but got '{result}' when AccountKey value has spaces: {whitespace_account_key_connection_string}"

    def test_extract_account_key_whitespace_only_string(self, whitespace_only_connection_string):
        """Test with connection string that is only whitespace."""
        with pytest.raises(ValueError, match="Connection string cannot be whitespace only"):
            _extract_account_key_from_connection_string(whitespace_only_connection_string)

    def test_extract_account_key_multiple_account_keys(self, multiple_account_key_connection_string):
        """Test with connection string containing multiple AccountKey parameters."""
        with pytest.raises(ValueError, match="Multiple AccountKey parameters found in connection string"):
            _extract_account_key_from_connection_string(multiple_account_key_connection_string)


class TestValidateAzureAccountKey:
    """Test cases for _validate_azure_account_key."""

    def test_validate_account_key_success(self, mock_blob_service_client):
        """Test successful account key validation."""
        # Mock successful list_containers operation
        mock_blob_service_client.list_containers.return_value = iter([])

        result = _validate_azure_account_key("testaccount", "validkey123")

        assert result is True, "Expected True for valid account key"
        mock_blob_service_client.list_containers.assert_called_once_with(timeout=5)

    def test_validate_account_key_auth_error(self, mock_blob_service_client):
        """Test account key validation with authentication error."""
        # Mock ClientAuthenticationError
        mock_blob_service_client.list_containers.side_effect = ClientAuthenticationError("Invalid credentials")

        result = _validate_azure_account_key("testaccount", "invalidkey")

        assert result is False, "Expected False for invalid account key"
        mock_blob_service_client.list_containers.assert_called_once_with(timeout=5)

    def test_validate_account_key_other_exception(self, mock_blob_service_client):
        """Test account key validation with other exceptions."""
        # Mock other exception
        mock_blob_service_client.list_containers.side_effect = Exception("Network error")

        with pytest.raises(Exception, match="Account key for account testaccount is invalid: Network error"):
            _validate_azure_account_key("testaccount", "problematickey")

    def test_validate_account_key_custom_timeout(self, mock_blob_service_client):
        """Test account key validation with custom timeout."""
        mock_blob_service_client.list_containers.return_value = iter([])

        result = _validate_azure_account_key("testaccount", "validkey123", conn_timeout=10)

        assert result is True, "Expected True for valid account key with custom timeout"
        mock_blob_service_client.list_containers.assert_called_once_with(timeout=10)


class TestValidateAzureStorageConfig:
    """Test cases for validate_azure_storage_config."""

    def test_validate_config_success(self, complete_valid_connection_string, mock_blob_service_client):
        """Test successful Azure Storage configuration validation."""
        # Mock successful validation
        mock_blob_service_client.list_containers.return_value = iter([])

        result = validate_azure_storage_config(complete_valid_connection_string)

        assert result["valid"] is True, f"Expected valid=True but got {result}"
        assert result["error"] is None, f"Expected no error but got {result['error']}"

    def test_validate_config_empty_connection_string(self):
        """Test validation with empty connection string."""
        with pytest.raises(ValueError, match="An Azure Storage connection string is required"):
            validate_azure_storage_config("")

    def test_validate_config_none_connection_string(self):
        """Test validation with None connection string."""
        with pytest.raises(ValueError, match="An Azure Storage connection string is required"):
            validate_azure_storage_config(None)

    def test_validate_config_malformed_connection_string(self):
        """Test validation with malformed connection string."""
        malformed_conn_str = "AccountName=test"  # Missing AccountKey

        result = validate_azure_storage_config(malformed_conn_str)

        assert result["valid"] is False, f"Expected valid=False but got {result}"
        assert (
            "Connection string validation failed" in result["error"]
        ), f"Expected connection string error but got {result['error']}"
        assert (
            "AccountKey parameter not found" in result["error"]
        ), f"Expected specific error about AccountKey but got {result['error']}"

    def test_validate_config_invalid_account_key(self, mock_blob_service_client):
        """Test validation with invalid account key."""
        # Mock authentication error
        mock_blob_service_client.list_containers.side_effect = ClientAuthenticationError("Invalid credentials")

        conn_str = "DefaultEndpointsProtocol=https;AccountName=testaccount;AccountKey=invalidkey;EndpointSuffix=core.windows.net"
        result = validate_azure_storage_config(conn_str)

        assert result["valid"] is False, f"Expected valid=False but got {result}"
        assert (
            result["error"] == "Account key is invalid"
        ), f"Expected 'Account key is invalid' but got {result['error']}"

    def test_validate_config_azure_exception(self, mock_blob_service_client):
        """Test validation with Azure service exception."""
        # Mock other Azure exception
        mock_blob_service_client.list_containers.side_effect = Exception("Azure service unavailable")

        conn_str = (
            "DefaultEndpointsProtocol=https;AccountName=testaccount;AccountKey=validkey;EndpointSuffix=core.windows.net"
        )
        result = validate_azure_storage_config(conn_str)

        assert result["valid"] is False, f"Expected valid=False but got {result}"
        assert (
            "Azure config validation failed" in result["error"]
        ), f"Expected Azure validation error but got {result['error']}"
        assert (
            "Azure service unavailable" in result["error"]
        ), f"Expected specific error message but got {result['error']}"

    def test_validate_config_empty_account_name(self):
        """Test validation with empty account name in connection string."""
        conn_str = "DefaultEndpointsProtocol=https;AccountName=;AccountKey=validkey;EndpointSuffix=core.windows.net"

        result = validate_azure_storage_config(conn_str)

        assert result["valid"] is False, f"Expected valid=False but got {result}"
        assert (
            "Connection string validation failed" in result["error"]
        ), f"Expected connection string error but got {result['error']}"
        assert (
            "AccountName parameter cannot be empty" in result["error"]
        ), f"Expected specific error about empty AccountName but got {result['error']}"

    def test_validate_config_empty_account_key(self):
        """Test validation with empty account key in connection string."""
        conn_str = "DefaultEndpointsProtocol=https;AccountName=testaccount;AccountKey=;EndpointSuffix=core.windows.net"

        result = validate_azure_storage_config(conn_str)

        assert result["valid"] is False, f"Expected valid=False but got {result}"
        assert (
            "Connection string validation failed" in result["error"]
        ), f"Expected connection string error but got {result['error']}"
        assert (
            "AccountKey parameter cannot be empty" in result["error"]
        ), f"Expected specific error about empty AccountKey but got {result['error']}"
