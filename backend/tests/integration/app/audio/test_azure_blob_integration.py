"""Integration tests for Azure Blob Storage operations."""

import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobServiceClient

# Import the actual functions we want to test


def create_blob_fast(blob_service_client, container_name: str, blob_name: str, file_path: Path) -> bool:
    """Fast blob creation using shared BlobServiceClient for testing."""
    try:
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        with file_path.open("rb") as data:
            blob_client.upload_blob(data, overwrite=True)
    except Exception:
        return False
    else:
        return True


def blob_exists_fast(blob_service_client, container_name: str, blob_name: str) -> bool:
    """Fast blob existence check using shared BlobServiceClient for testing."""
    try:
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        return blob_client.exists()
    except Exception:
        return False


def delete_blob_fast(blob_service_client, container_name: str, blob_name: str) -> bool:
    """Fast blob deletion using shared BlobServiceClient for testing."""
    try:
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        blob_client.delete_blob(delete_snapshots="include")
    except ResourceNotFoundError:
        return False
    except Exception:
        return False
    else:
        return True


@pytest.mark.integration
class TestAzureBlobOperations:
    """Integration tests for Azure Blob Storage operations."""

    @pytest.fixture(scope="class")
    def connection_string(self):
        """Get connection string from environment."""
        conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not conn_str:
            pytest.skip("AZURE_STORAGE_CONNECTION_STRING environment variable not set")
        return conn_str

    @pytest.fixture(scope="class")
    def blob_service_client(self, connection_string):
        """Shared BlobServiceClient for connection verification."""
        return BlobServiceClient.from_connection_string(connection_string)

    @pytest.fixture(autouse=True)
    def setup(self, connection_string):
        """Setup test configuration."""
        # Azure Storage configuration
        self.account_name = "justicetransdevstor"
        self.container_name = "application-data"
        self.test_subdirectory = "tests"  # Use subdirectory to avoid clutter
        self.connection_string = connection_string

        # Store connection info for debugging if needed
        self._debug_info = {
            "account": self.account_name,
            "container": self.container_name,
            "subdirectory": self.test_subdirectory,
            "connection_start": self.connection_string[:20] + "..."
        }

    def test_connection_and_container_access(self, blob_service_client):
        """Test basic connection to Azure Storage and container access."""
        try:
            # Just check if we can access the specific container (much faster than listing all)
            container_client = blob_service_client.get_container_client(self.container_name)
            container_client.get_container_properties()
            assert True  # If no exception, it's accessible
        except Exception as e:
            pytest.fail(f"Failed to connect to Azure Storage or access container '{self.container_name}': {e}")

    @pytest.fixture(scope="class")
    def shared_test_blob_name(self):
        """Generate shared blob name for create/delete test pair."""
        return "test-blob-shared.txt"  # Static name for create/delete pair

    @pytest.fixture
    def temp_file(self, test_file_content):
        """Create temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(test_file_content)
            temp_file_path = Path(f.name)
        yield temp_file_path
        if temp_file_path.exists():
            temp_file_path.unlink()

    @pytest.fixture
    def test_file_content(self):
        """Test file content."""
        return f"Integration Test File\nContent created at: {datetime.now(tz=UTC).isoformat()}"

    def test_create_blob(self, temp_file, shared_test_blob_name, blob_service_client):
        """Test creating a blob and verifying it exists - does NOT delete it."""
        # Create blob path with subdirectory
        blob_path = f"{self.test_subdirectory}/{shared_test_blob_name}"

        # Create the blob using fast helper
        success = create_blob_fast(
            blob_service_client=blob_service_client,
            container_name=self.container_name,
            blob_name=blob_path,
            file_path=temp_file
        )
        assert success, "Failed to create blob using fast helper"

        # Verify it exists using fast helper
        exists = blob_exists_fast(
            blob_service_client=blob_service_client,
            container_name=self.container_name,
            blob_name=blob_path
        )
        assert exists, "Blob should exist after creation"

    def test_delete_blob(self, shared_test_blob_name, blob_service_client):
        """Test deleting a blob and verifying it's gone - assumes blob already exists."""
        # Create blob path with subdirectory
        blob_path = f"{self.test_subdirectory}/{shared_test_blob_name}"

        # First verify the blob exists (should have been created by previous test)
        exists_before = blob_exists_fast(
            blob_service_client=blob_service_client,
            container_name=self.container_name,
            blob_name=blob_path
        )
        assert exists_before, f"Blob should exist before deletion: {blob_path}"

        # Delete the blob using fast helper
        deleted = delete_blob_fast(
            blob_service_client=blob_service_client,
            container_name=self.container_name,
            blob_name=blob_path
        )
        assert deleted, "Failed to delete blob using fast helper"

        # Verify it no longer exists
        exists_after = blob_exists_fast(
            blob_service_client=blob_service_client,
            container_name=self.container_name,
            blob_name=blob_path
        )
        assert not exists_after, "Blob should not exist after deletion"
