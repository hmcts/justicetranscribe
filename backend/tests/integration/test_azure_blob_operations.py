"""Integration tests for Azure Blob Storage operations."""

import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobServiceClient

# Import the actual functions we want to test
from app.audio.azure_utils import AzureBlobManager


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
    """Integration tests for Azure Blob Storage operations using azure_utils.py functions."""

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
        self.connection_string = connection_string

        # Store connection info for debugging if needed
        self._debug_info = {
            "account": self.account_name,
            "container": self.container_name,
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

    @pytest.fixture
    def test_blob_name(self):
        """Generate unique blob name for each test."""
        timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S_%f")
        return f"test-blob-{timestamp}.txt"

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

    def test_create_and_verify_blob_sync(self, temp_file, test_blob_name, blob_service_client):
        """Test creating a blob and verifying it exists using fast helper functions."""
        # Create the blob using fast helper (for speed)
        success = create_blob_fast(
            blob_service_client=blob_service_client,
            container_name=self.container_name,
            blob_name=test_blob_name,
            file_path=temp_file
        )
        assert success, "Failed to create blob using fast helper"

        # Verify it exists using fast helper
        exists = blob_exists_fast(
            blob_service_client=blob_service_client,
            container_name=self.container_name,
            blob_name=test_blob_name
        )
        assert exists, "Blob should exist after creation"


    def test_delete_blob_sync(self, temp_file, test_blob_name, blob_service_client):
        """Test deleting a blob using fast helper functions."""
        # First create the blob using fast helper
        success = create_blob_fast(
            blob_service_client=blob_service_client,
            container_name=self.container_name,
            blob_name=test_blob_name,
            file_path=temp_file
        )
        assert success, "Failed to create blob for deletion test"

        # Verify it exists before deletion
        exists_before = blob_exists_fast(
            blob_service_client=blob_service_client,
            container_name=self.container_name,
            blob_name=test_blob_name
        )
        assert exists_before, "Blob should exist before deletion"

        # Delete the blob using fast helper
        deleted = delete_blob_fast(
            blob_service_client=blob_service_client,
            container_name=self.container_name,
            blob_name=test_blob_name
        )
        assert deleted, "Failed to delete blob using fast helper"

        # Verify it no longer exists
        exists_after = blob_exists_fast(
            blob_service_client=blob_service_client,
            container_name=self.container_name,
            blob_name=test_blob_name
        )
        assert not exists_after, "Blob should not exist after deletion"

    def test_complete_blob_lifecycle_sync(self, temp_file, test_blob_name, blob_service_client):
        """Test complete blob lifecycle using fast helper functions."""
        # Step 1: Create blob using fast helper
        success = create_blob_fast(
            blob_service_client=blob_service_client,
            container_name=self.container_name,
            blob_name=test_blob_name,
            file_path=temp_file
        )
        assert success, "Failed to create blob"

        # Step 2: Verify blob exists
        exists_after_create = blob_exists_fast(
            blob_service_client=blob_service_client,
            container_name=self.container_name,
            blob_name=test_blob_name
        )
        assert exists_after_create, "Blob should exist after creation"

        # Step 3: Delete blob using fast helper
        deleted = delete_blob_fast(
            blob_service_client=blob_service_client,
            container_name=self.container_name,
            blob_name=test_blob_name
        )
        assert deleted, "Failed to delete blob"

        # Step 4: Verify blob no longer exists
        exists_after_delete = blob_exists_fast(
            blob_service_client=blob_service_client,
            container_name=self.container_name,
            blob_name=test_blob_name
        )
        assert not exists_after_delete, "Blob should not exist after deletion"

    def test_delete_nonexistent_blob_sync(self, test_blob_name, blob_service_client):
        """Test that deleting a non-existent blob handles gracefully."""
        # Try to delete a blob that doesn't exist using fast helper
        deleted = delete_blob_fast(
            blob_service_client=blob_service_client,
            container_name=self.container_name,
            blob_name=f"nonexistent-{test_blob_name}"
        )

        # Should return False for non-existent blob, not raise exception
        assert not deleted, "Deleting non-existent blob should return False"

    def test_blob_overwrite_sync(self, temp_file, test_blob_name, blob_service_client):
        """Test that uploading to the same blob name overwrites the content."""
        # Create first blob using fast helper
        success1 = create_blob_fast(
            blob_service_client=blob_service_client,
            container_name=self.container_name,
            blob_name=test_blob_name,
            file_path=temp_file
        )
        assert success1, "Failed to create first blob"

        # Create second blob with same name (should overwrite)
        success2 = create_blob_fast(
            blob_service_client=blob_service_client,
            container_name=self.container_name,
            blob_name=test_blob_name,
            file_path=temp_file
        )
        assert success2, "Failed to overwrite blob"

        # Verify blob still exists
        exists = blob_exists_fast(
            blob_service_client=blob_service_client,
            container_name=self.container_name,
            blob_name=test_blob_name
        )
        assert exists, "Blob should exist after overwrite"

        # Cleanup using fast helper
        delete_blob_fast(
            blob_service_client=blob_service_client,
            container_name=self.container_name,
            blob_name=test_blob_name
        )


    @pytest.mark.slow
    def test_azure_blob_manager_class(self, temp_file, test_blob_name):
        """Test the AzureBlobManager class methods."""
        # Create manager instance
        manager = AzureBlobManager(connection_string=self.connection_string)

        # Test create
        success = manager.create_blob_from_file(
            file_path=temp_file,
            blob_name=test_blob_name,
            container_name=self.container_name
        )
        assert success, "Failed to create blob using AzureBlobManager"

        # Test exists
        exists = manager.blob_exists(
            blob_name=test_blob_name,
            container_name=self.container_name
        )
        assert exists, "Blob should exist using AzureBlobManager"

        # Test delete
        deleted = manager.delete_blob(
            blob_name=test_blob_name,
            container_name=self.container_name
        )
        assert deleted, "Failed to delete blob using AzureBlobManager"

        # Verify deletion
        exists_after = manager.blob_exists(
            blob_name=test_blob_name,
            container_name=self.container_name
        )
        assert not exists_after, "Blob should not exist after deletion using AzureBlobManager"
