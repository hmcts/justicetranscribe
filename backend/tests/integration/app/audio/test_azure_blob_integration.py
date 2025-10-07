"""Integration tests for Azure Blob Storage operations."""

import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

# Import the actual functions we want to test
from app.audio.azure_utils import AzureBlobManager


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

    def test_connection_and_container_access(self, connection_string):
        """Test basic connection to Azure Storage using AzureBlobManager."""
        try:
            # Test connection by creating a manager instance (this validates the connection string)
            manager = AzureBlobManager(connection_string=connection_string)
            # Try a simple operation that requires authentication
            # We'll just check if we can create a manager without errors
            assert manager.connection_string == connection_string
            assert manager.container_name is not None
            assert manager.account_name is not None
        except Exception as e:
            pytest.fail(f"Failed to create AzureBlobManager with connection string: {e}")

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

    def test_create_blob(self, temp_file, shared_test_blob_name, connection_string):
        """Test creating a blob and verifying it exists - does NOT delete it."""
        # Create blob path with subdirectory
        blob_path = f"{self.test_subdirectory}/{shared_test_blob_name}"

        # # Create the blob using AzureBlobManager (tests production code)
        # success = create_blob_with_manager(
        #     connection_string=connection_string,
        #     container_name=self.container_name,
        #     blob_name=blob_path,
        #     file_path=temp_file
        # )

        manager = AzureBlobManager(connection_string=connection_string)
        success = manager.create_blob_from_file(
            file_path=temp_file,
            blob_name=blob_path,
            container_name=self.container_name
        )
        assert success, "Failed to create blob using AzureBlobManager"

        # Verify it exists using AzureBlobManager (tests production code)
        manager = AzureBlobManager(connection_string=connection_string)
        exists = manager.blob_exists(
            blob_name=blob_path,
            container_name=self.container_name
        )
        assert exists, "Blob should exist after creation"

    def test_delete_blob(self, shared_test_blob_name, connection_string):
        """Test deleting a blob and verifying it's gone - assumes blob already exists."""
        # Create blob path with subdirectory
        blob_path = f"{self.test_subdirectory}/{shared_test_blob_name}"

        # First verify the blob exists (should have been created by previous test)
        manager = AzureBlobManager(connection_string=connection_string)
        exists_before = manager.blob_exists(
            blob_name=blob_path,
            container_name=self.container_name
        )
        assert exists_before, f"Blob should exist before deletion: {blob_path}"

        # Delete the blob using AzureBlobManager (tests production code)
        deleted = manager.delete_blob(
            blob_name=blob_path,
            container_name=self.container_name
        )
        assert deleted, "Failed to delete blob using AzureBlobManager"

        # Verify it no longer exists
        exists_after = manager.blob_exists(
            blob_name=blob_path,
            container_name=self.container_name
        )
        assert not exists_after, "Blob should not exist after deletion"
