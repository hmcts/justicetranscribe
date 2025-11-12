"""Test Azure Storage utilities for transcription upload to Azure Blob Storage."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from azure.core.exceptions import ClientAuthenticationError, ResourceExistsError, ResourceNotFoundError

from app.audio.azure_utils import (
    AsyncAzureBlobManager,
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


# =============================================================================
# AsyncAzureBlobManager Unit Tests
# =============================================================================

@pytest.mark.asyncio
class TestAsyncAzureBlobManager:
    """Test cases for AsyncAzureBlobManager class."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("app.audio.azure_utils.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.AZURE_STORAGE_CONNECTION_STRING = "test_connection_string"
            mock_settings.AZURE_STORAGE_ACCOUNT_NAME = "test_account"
            mock_settings.AZURE_STORAGE_CONTAINER_NAME = "test_container"
            mock_get_settings.return_value = mock_settings
            yield mock_settings

    @pytest.fixture
    def async_blob_manager(self, mock_settings):  # noqa: ARG002
        """Create AsyncAzureBlobManager instance for testing."""
        return AsyncAzureBlobManager()

    @pytest.fixture
    def sample_file_path(self, tmp_path):
        """Create a sample file for testing."""
        file_path = tmp_path / "test_file.txt"
        file_path.write_text("test content")
        return file_path

    @pytest.fixture
    def mock_async_context_manager(self):
        """Create a proper async context manager mock."""
        class AsyncContextManagerMock:
            def __init__(self, obj_to_return):
                self.obj = obj_to_return

            async def __aenter__(self):
                return self.obj

            async def __aexit__(self, exc_type, exc, tb):
                return None

        return AsyncContextManagerMock

    @patch("app.audio.azure_utils.AsyncBlobServiceClient")
    @patch("app.audio.azure_utils.logger")
    async def test_create_blob_from_file_success(self, mock_logger, mock_async_blob_service_client_class, async_blob_manager, sample_file_path, mock_async_context_manager):
        """Test successful async blob creation with proper async mocking."""
        # Setup mocks using the proper async patterns
        mock_blob_service_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_container_client = MagicMock()

        # Configure the async context manager
        mock_async_blob_service_client_class.from_connection_string.return_value = mock_async_context_manager(mock_blob_service_client)
        mock_blob_service_client.get_blob_client.return_value = mock_blob_client
        mock_blob_service_client.get_container_client.return_value = mock_container_client

        # Mock container existence check
        mock_container_client.exists = AsyncMock(return_value=True)

        # Configure async methods properly - upload_blob is awaited in the async code
        mock_blob_client.upload_blob = AsyncMock()  # This needs to be AsyncMock since it's awaited

        # Test
        result = await async_blob_manager.create_blob_from_file(sample_file_path, "test_blob.txt")

        # Assertions
        assert result is True, "create_blob_from_file should return True on success"
        # from_connection_string is called twice: once for container check, once for blob upload
        assert mock_async_blob_service_client_class.from_connection_string.call_count == 2
        mock_blob_service_client.get_blob_client.assert_called_once_with(
            container="test_container",
            blob="test_blob.txt"
        )
        mock_blob_client.upload_blob.assert_awaited_once()
        mock_logger.info.assert_called_once_with("Successfully created blob: test_container/test_blob.txt")

    @patch("app.audio.azure_utils.AsyncBlobServiceClient")
    async def test_create_blob_from_file_file_not_found(self, mock_async_blob_service_client_class, async_blob_manager, mock_async_context_manager, caplog):
        """Test async blob creation when file doesn't exist."""
        # Setup mocks for container existence check
        mock_blob_service_client = MagicMock()
        mock_container_client = MagicMock()
        mock_async_blob_service_client_class.from_connection_string.return_value = mock_async_context_manager(mock_blob_service_client)
        mock_blob_service_client.get_container_client.return_value = mock_container_client

        # Mock container existence check
        mock_container_client.exists = AsyncMock(return_value=True)

        # Test - FileNotFoundError will be raised when trying to open the file
        result = await async_blob_manager.create_blob_from_file(Path("nonexistent.txt"), "test_blob.txt")

        # Assertions
        assert result is False, "create_blob_from_file should return False when file doesn't exist"
        assert "File not found: nonexistent.txt" in caplog.text, "Should log file not found error"

    @patch("app.audio.azure_utils.AsyncBlobServiceClient")
    async def test_create_blob_from_file_resource_exists_error(self, mock_async_blob_service_client_class, async_blob_manager, sample_file_path, mock_async_context_manager, caplog):
        """Test async blob creation when blob already exists."""
        # Setup mocks
        mock_blob_service_client = MagicMock()
        mock_container_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_async_blob_service_client_class.from_connection_string.return_value = mock_async_context_manager(mock_blob_service_client)
        mock_blob_service_client.get_container_client.return_value = mock_container_client
        mock_blob_service_client.get_blob_client.return_value = mock_blob_client

        # Mock container existence check
        mock_container_client.exists = AsyncMock(return_value=True)

        mock_blob_client.upload_blob = AsyncMock(side_effect=ResourceExistsError("Blob already exists"))

        # Test
        result = await async_blob_manager.create_blob_from_file(sample_file_path, "test_blob.txt")

        # Assertions
        assert result is False, "create_blob_from_file should return False when blob already exists"
        assert "Blob already exists: test_container/test_blob.txt" in caplog.text, "Should log blob already exists warning"

    @patch("app.audio.azure_utils.AsyncBlobServiceClient")
    async def test_create_blob_from_file_general_exception(self, mock_async_blob_service_client_class, async_blob_manager, sample_file_path, mock_async_context_manager, caplog):
        """Test async blob creation with general exception."""
        # Setup mocks
        mock_blob_service_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_container_client = MagicMock()
        mock_async_blob_service_client_class.from_connection_string.return_value = mock_async_context_manager(mock_blob_service_client)
        mock_blob_service_client.get_blob_client.return_value = mock_blob_client
        mock_blob_service_client.get_container_client.return_value = mock_container_client

        # Mock container existence check
        mock_container_client.exists = AsyncMock(return_value=True)

        mock_blob_client.upload_blob = AsyncMock(side_effect=Exception("General error"))

        # Test
        result = await async_blob_manager.create_blob_from_file(sample_file_path, "test_blob.txt")

        # Assertions
        assert result is False, "create_blob_from_file should return False on general exception"
        assert "Failed to create blob test_container/test_blob.txt: General error" in caplog.text, "Should log general error"

    @patch("app.audio.azure_utils.AsyncBlobServiceClient")
    @patch("app.audio.azure_utils.logger")
    async def test_delete_blob_success(self, mock_logger, mock_async_blob_service_client_class, async_blob_manager, mock_async_context_manager):
        """Test successful async blob deletion."""
        # Setup mocks
        mock_blob_service_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_async_blob_service_client_class.from_connection_string.return_value = mock_async_context_manager(mock_blob_service_client)
        mock_blob_service_client.get_blob_client.return_value = mock_blob_client

        # Configure async methods properly - delete_blob is awaited in the async code
        mock_blob_client.delete_blob = AsyncMock()  # This needs to be AsyncMock since it's awaited

        # Test
        result = await async_blob_manager.delete_blob("test_blob.txt")

        # Assertions
        assert result is True, "delete_blob should return True on success"
        mock_blob_client.delete_blob.assert_awaited_once_with(delete_snapshots="include")
        mock_logger.info.assert_called_once_with("Successfully deleted blob: test_container/test_blob.txt")

    @patch("app.audio.azure_utils.AsyncBlobServiceClient")
    async def test_delete_blob_not_found(self, mock_async_blob_service_client_class, async_blob_manager, mock_async_context_manager, caplog):
        """Test async blob deletion when blob doesn't exist."""
        # Setup mocks
        mock_blob_service_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_async_blob_service_client_class.from_connection_string.return_value = mock_async_context_manager(mock_blob_service_client)
        mock_blob_service_client.get_blob_client.return_value = mock_blob_client
        mock_blob_client.delete_blob = AsyncMock(side_effect=ResourceNotFoundError("Blob not found"))

        # Test
        result = await async_blob_manager.delete_blob("test_blob.txt")

        # Assertions
        assert result is False, "delete_blob should return False when blob not found"
        assert "Blob not found: test_container/test_blob.txt" in caplog.text, "Should log blob not found warning"

    @patch("app.audio.azure_utils.AsyncBlobServiceClient")
    async def test_delete_blob_general_exception(self, mock_async_blob_service_client_class, async_blob_manager, mock_async_context_manager, caplog):
        """Test async blob deletion with general exception."""
        # Setup mocks
        mock_blob_service_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_async_blob_service_client_class.from_connection_string.return_value = mock_async_context_manager(mock_blob_service_client)
        mock_blob_service_client.get_blob_client.return_value = mock_blob_client
        mock_blob_client.delete_blob = AsyncMock(side_effect=Exception("General error"))

        # Test
        result = await async_blob_manager.delete_blob("test_blob.txt")

        # Assertions
        assert result is False, "delete_blob should return False on general exception"
        assert "Failed to delete blob test_container/test_blob.txt: General error" in caplog.text, "Should log general error"

    @patch("app.audio.azure_utils.AsyncBlobServiceClient")
    async def test_blob_exists_true(self, mock_async_blob_service_client_class, async_blob_manager, mock_async_context_manager):
        """Test async blob existence check when blob exists."""
        # Setup mocks
        mock_blob_service_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_async_blob_service_client_class.from_connection_string.return_value = mock_async_context_manager(mock_blob_service_client)
        mock_blob_service_client.get_blob_client.return_value = mock_blob_client
        # exists() is awaited in the async code, so it needs to be AsyncMock
        mock_blob_client.exists = AsyncMock(return_value=True)

        # Test
        result = await async_blob_manager.blob_exists("test_blob.txt")

        # Assertions
        assert result is True, "blob_exists should return True when blob exists"
        mock_blob_client.exists.assert_awaited_once()

    @patch("app.audio.azure_utils.AsyncBlobServiceClient")
    async def test_blob_exists_false(self, mock_async_blob_service_client_class, async_blob_manager, mock_async_context_manager):
        """Test async blob existence check when blob doesn't exist."""
        # Setup mocks
        mock_blob_service_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_async_blob_service_client_class.from_connection_string.return_value = mock_async_context_manager(mock_blob_service_client)
        mock_blob_service_client.get_blob_client.return_value = mock_blob_client
        # exists() is awaited in the async code, so it needs to be AsyncMock
        mock_blob_client.exists = AsyncMock(return_value=False)

        # Test
        result = await async_blob_manager.blob_exists("test_blob.txt")

        # Assertions
        assert result is False, "blob_exists should return False when blob doesn't exist"

    @patch("app.audio.azure_utils.AsyncBlobServiceClient")
    async def test_blob_exists_exception(self, mock_async_blob_service_client_class, async_blob_manager, mock_async_context_manager, caplog):
        """Test async blob existence check with exception."""
        # Setup mocks
        mock_blob_service_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_async_blob_service_client_class.from_connection_string.return_value = mock_async_context_manager(mock_blob_service_client)
        mock_blob_service_client.get_blob_client.return_value = mock_blob_client
        mock_blob_client.exists = AsyncMock(side_effect=Exception("General error"))

        # Test
        result = await async_blob_manager.blob_exists("test_blob.txt")

        # Assertions
        assert result is False, "blob_exists should return False on general exception"
        assert "Failed to check if blob exists test_container/test_blob.txt: General error" in caplog.text, "Should log general error"

    @patch("app.audio.azure_utils.AsyncBlobServiceClient")
    @patch("app.audio.azure_utils.logger")
    async def test_list_blobs_in_prefix_success(self, mock_logger, mock_async_blob_service_client_class, async_blob_manager, mock_async_context_manager):
        """Test successful listing of blobs with a prefix."""
        # Setup mocks
        mock_blob_service_client = MagicMock()
        mock_container_client = MagicMock()
        mock_async_blob_service_client_class.from_connection_string.return_value = mock_async_context_manager(mock_blob_service_client)
        mock_blob_service_client.get_container_client.return_value = mock_container_client

        # Mock container existence check
        mock_container_client.exists = AsyncMock(return_value=True)

        # Mock blob items returned from list_blobs
        mock_blob1 = MagicMock()
        mock_blob1.name = "user-uploads/test@example.com/file1.mp4"
        mock_blob1.last_modified = "2024-01-01T12:00:00Z"
        mock_blob1.size = 1024
        mock_blob1.metadata = {"processed": "false"}

        mock_blob2 = MagicMock()
        mock_blob2.name = "user-uploads/test@example.com/file2.mp4"
        mock_blob2.last_modified = "2024-01-02T12:00:00Z"
        mock_blob2.size = 2048
        mock_blob2.metadata = None

        # list_blobs returns an async iterable
        async def mock_list_blobs(*args, **kwargs):  # noqa: ARG001
            for blob in [mock_blob1, mock_blob2]:
                yield blob

        mock_container_client.list_blobs = mock_list_blobs

        # Test
        result = await async_blob_manager.list_blobs_in_prefix("user-uploads/")

        # Assertions
        assert len(result) == 2, "Should return 2 blobs"
        assert result[0]["name"] == "user-uploads/test@example.com/file1.mp4"
        assert result[0]["metadata"] == {"processed": "false"}
        assert result[1]["name"] == "user-uploads/test@example.com/file2.mp4"
        assert result[1]["metadata"] == {}  # None should be converted to {}
        mock_logger.info.assert_called_once_with("Listed 2 blobs with prefix 'user-uploads/' in container 'test_container'")

    @patch("app.audio.azure_utils.AsyncBlobServiceClient")
    @patch("app.audio.azure_utils.logger")
    async def test_list_blobs_in_prefix_empty(self, mock_logger, mock_async_blob_service_client_class, async_blob_manager, mock_async_context_manager):
        """Test listing blobs when no blobs match the prefix."""
        # Setup mocks
        mock_blob_service_client = MagicMock()
        mock_container_client = MagicMock()
        mock_async_blob_service_client_class.from_connection_string.return_value = mock_async_context_manager(mock_blob_service_client)
        mock_blob_service_client.get_container_client.return_value = mock_container_client

        # Mock container existence check
        mock_container_client.exists = AsyncMock(return_value=True)

        # list_blobs returns empty async iterable
        async def mock_list_blobs(*args, **kwargs):  # noqa: ARG001
            # Empty async generator
            if False:  # Never executes, but makes it a generator
                yield

        mock_container_client.list_blobs = mock_list_blobs

        # Test
        result = await async_blob_manager.list_blobs_in_prefix("nonexistent-prefix/")

        # Assertions
        assert len(result) == 0, "Should return empty list"
        # No log message when no blobs are found (to reduce noise during polling)
        mock_logger.info.assert_not_called()

    @patch("app.audio.azure_utils.AsyncBlobServiceClient")
    async def test_list_blobs_in_prefix_exception(self, mock_async_blob_service_client_class, async_blob_manager, mock_async_context_manager, caplog):
        """Test listing blobs with exception."""
        # Setup mocks
        mock_blob_service_client = MagicMock()
        mock_container_client = MagicMock()
        mock_async_blob_service_client_class.from_connection_string.return_value = mock_async_context_manager(mock_blob_service_client)
        mock_blob_service_client.get_container_client.return_value = mock_container_client

        # Mock container existence check
        mock_container_client.exists = AsyncMock(return_value=True)

        # list_blobs raises exception
        async def mock_list_blobs(*args, **kwargs):  # noqa: ARG001
            error_msg = "List error"
            raise RuntimeError(error_msg)
            yield  # Make it a generator # noqa: RET502, RUF100

        mock_container_client.list_blobs = mock_list_blobs

        # Test
        result = await async_blob_manager.list_blobs_in_prefix("user-uploads/")

        # Assertions
        assert result == [], "Should return empty list on exception"
        assert "Failed to list blobs with prefix 'user-uploads/' in container 'test_container': List error" in caplog.text

    @patch("app.audio.azure_utils.AsyncBlobServiceClient")
    async def test_get_blob_metadata_success(self, mock_async_blob_service_client_class, async_blob_manager, mock_async_context_manager):
        """Test successful retrieval of blob metadata."""
        # Setup mocks
        mock_blob_service_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_async_blob_service_client_class.from_connection_string.return_value = mock_async_context_manager(mock_blob_service_client)
        mock_blob_service_client.get_blob_client.return_value = mock_blob_client

        # Mock blob properties
        mock_properties = MagicMock()
        mock_properties.metadata = {"processed": "true", "processed_at": "2024-01-01T12:00:00Z"}
        mock_blob_client.get_blob_properties = AsyncMock(return_value=mock_properties)

        # Test
        result = await async_blob_manager.get_blob_metadata("user-uploads/test@example.com/file.mp4")

        # Assertions
        assert result == {"processed": "true", "processed_at": "2024-01-01T12:00:00Z"}
        mock_blob_client.get_blob_properties.assert_awaited_once()

    @patch("app.audio.azure_utils.AsyncBlobServiceClient")
    async def test_get_blob_metadata_none(self, mock_async_blob_service_client_class, async_blob_manager, mock_async_context_manager):
        """Test retrieval of blob metadata when metadata is None."""
        # Setup mocks
        mock_blob_service_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_async_blob_service_client_class.from_connection_string.return_value = mock_async_context_manager(mock_blob_service_client)
        mock_blob_service_client.get_blob_client.return_value = mock_blob_client

        # Mock blob properties with None metadata
        mock_properties = MagicMock()
        mock_properties.metadata = None
        mock_blob_client.get_blob_properties = AsyncMock(return_value=mock_properties)

        # Test
        result = await async_blob_manager.get_blob_metadata("user-uploads/test@example.com/file.mp4")

        # Assertions
        assert result == {}, "Should return empty dict when metadata is None"

    @patch("app.audio.azure_utils.AsyncBlobServiceClient")
    async def test_get_blob_metadata_not_found(self, mock_async_blob_service_client_class, async_blob_manager, mock_async_context_manager, caplog):
        """Test retrieval of blob metadata when blob doesn't exist."""
        # Setup mocks
        mock_blob_service_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_async_blob_service_client_class.from_connection_string.return_value = mock_async_context_manager(mock_blob_service_client)
        mock_blob_service_client.get_blob_client.return_value = mock_blob_client
        mock_blob_client.get_blob_properties = AsyncMock(side_effect=ResourceNotFoundError("Blob not found"))

        # Test
        result = await async_blob_manager.get_blob_metadata("nonexistent.mp4")

        # Assertions
        assert result == {}, "Should return empty dict when blob not found"
        assert "Blob not found when getting metadata: test_container/nonexistent.mp4" in caplog.text

    @patch("app.audio.azure_utils.AsyncBlobServiceClient")
    async def test_get_blob_metadata_exception(self, mock_async_blob_service_client_class, async_blob_manager, mock_async_context_manager, caplog):
        """Test retrieval of blob metadata with general exception."""
        # Setup mocks
        mock_blob_service_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_async_blob_service_client_class.from_connection_string.return_value = mock_async_context_manager(mock_blob_service_client)
        mock_blob_service_client.get_blob_client.return_value = mock_blob_client
        mock_blob_client.get_blob_properties = AsyncMock(side_effect=Exception("General error"))

        # Test
        result = await async_blob_manager.get_blob_metadata("test.mp4")

        # Assertions
        assert result == {}, "Should return empty dict on exception"
        assert "Failed to get metadata for blob test_container/test.mp4: General error" in caplog.text

    @patch("app.audio.azure_utils.AsyncBlobServiceClient")
    @patch("app.audio.azure_utils.logger")
    async def test_set_blob_metadata_success(self, mock_logger, mock_async_blob_service_client_class, async_blob_manager, mock_async_context_manager):
        """Test successful setting of blob metadata."""
        # Setup mocks
        mock_blob_service_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_container_client = MagicMock()
        mock_async_blob_service_client_class.from_connection_string.return_value = mock_async_context_manager(mock_blob_service_client)
        mock_blob_service_client.get_blob_client.return_value = mock_blob_client
        mock_blob_service_client.get_container_client.return_value = mock_container_client

        # Mock container existence check
        mock_container_client.exists = AsyncMock(return_value=True)

        mock_blob_client.set_blob_metadata = AsyncMock()

        # Test
        metadata = {"processed": "true", "processed_at": "2024-01-01T12:00:00Z"}
        result = await async_blob_manager.set_blob_metadata("user-uploads/test@example.com/file.mp4", metadata)

        # Assertions
        assert result is True, "set_blob_metadata should return True on success"
        mock_blob_client.set_blob_metadata.assert_awaited_once_with(metadata=metadata)
        mock_logger.info.assert_called_once_with("Successfully set metadata on blob: test_container/user-uploads/test@example.com/file.mp4")

    @patch("app.audio.azure_utils.AsyncBlobServiceClient")
    async def test_set_blob_metadata_not_found(self, mock_async_blob_service_client_class, async_blob_manager, mock_async_context_manager, caplog):
        """Test setting blob metadata when blob doesn't exist."""
        # Setup mocks
        mock_blob_service_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_container_client = MagicMock()
        mock_async_blob_service_client_class.from_connection_string.return_value = mock_async_context_manager(mock_blob_service_client)
        mock_blob_service_client.get_blob_client.return_value = mock_blob_client
        mock_blob_service_client.get_container_client.return_value = mock_container_client

        # Mock container existence check
        mock_container_client.exists = AsyncMock(return_value=True)

        mock_blob_client.set_blob_metadata = AsyncMock(side_effect=ResourceNotFoundError("Blob not found"))

        # Test
        result = await async_blob_manager.set_blob_metadata("nonexistent.mp4", {"key": "value"})

        # Assertions
        assert result is False, "set_blob_metadata should return False when blob not found"
        assert "Blob not found when setting metadata: test_container/nonexistent.mp4" in caplog.text

    @patch("app.audio.azure_utils.AsyncBlobServiceClient")
    async def test_set_blob_metadata_exception(self, mock_async_blob_service_client_class, async_blob_manager, mock_async_context_manager, caplog):
        """Test setting blob metadata with general exception."""
        # Setup mocks
        mock_blob_service_client = MagicMock()
        mock_blob_client = MagicMock()
        mock_container_client = MagicMock()
        mock_async_blob_service_client_class.from_connection_string.return_value = mock_async_context_manager(mock_blob_service_client)
        mock_blob_service_client.get_blob_client.return_value = mock_blob_client
        mock_blob_service_client.get_container_client.return_value = mock_container_client

        # Mock container existence check
        mock_container_client.exists = AsyncMock(return_value=True)

        mock_blob_client.set_blob_metadata = AsyncMock(side_effect=Exception("General error"))

        # Test
        result = await async_blob_manager.set_blob_metadata("test.mp4", {"key": "value"})

        # Assertions
        assert result is False, "set_blob_metadata should return False on exception"
        assert "Failed to set metadata on blob test_container/test.mp4: General error" in caplog.text


