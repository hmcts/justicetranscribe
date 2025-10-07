"""Azure Storage utilities for connection management and blob operations."""

from pathlib import Path

from azure.core.exceptions import ClientAuthenticationError, ResourceExistsError, ResourceNotFoundError
from azure.storage.blob import BlobClient, BlobServiceClient
from azure.storage.blob.aio import BlobServiceClient as AsyncBlobServiceClient

from app.logger import logger
from utils.settings import get_settings


def _validate_azure_account_key(account_name: str, account_key: str, conn_timeout: int = 5) -> bool:
    """Validate that the Azure Storage account key is current and active.

    Parameters
    ----------
    account_name : str
        The Azure Storage account name.
    account_key : str
        The Azure Storage account key to validate.
    conn_timeout : int, optional
        Connection timeout in seconds. Default is 5.

    Returns
    -------
    bool
        True if the account key is valid, False otherwise.
    """

    try:
        # Create a BlobServiceClient with the account name and key
        blob_service_client = BlobServiceClient(
            account_url=f"https://{account_name}.blob.core.windows.net",
            credential=account_key,
            connection_timeout=conn_timeout,
        )

        # Attempt a simple operation requiring auth
        list(blob_service_client.list_containers(timeout=conn_timeout))
    except ClientAuthenticationError:
        # Case where account name is found but key is invalid
        return False
    except Exception as e:
        msg = f"Account key for account {account_name} is invalid: {e!s}"
        raise ValueError(msg) from e
    else:
        return True



def _extract_parameter_from_connection_string(
    connection_string: str,
    parameter_name: str
    ) -> str:
    """Extract a parameter value from an Azure Storage connection string.

    Parameters
    ----------
    connection_string : str
        The Azure Storage connection string.
    parameter_name : str
        The parameter name to extract (e.g., 'AccountName', 'AccountKey').

    Returns
    -------
    str
        The parameter value extracted from the connection string.

    Raises
    ------
    ValueError
        If the connection string is empty, malformed, or missing the parameter.
    """
    if not connection_string:
        msg = "Connection string cannot be empty"
        raise ValueError(msg)

    if not connection_string.strip():
        msg = "Connection string cannot be whitespace only"
        raise ValueError(msg)

    # Split by semicolon and look for the specified parameter
    parameter_found = False
    parameter_value = None
    parameter_prefix = f"{parameter_name}="

    for part_raw in connection_string.split(";"):
        part = part_raw.strip()  # Remove leading/trailing whitespace from each part

        if part.startswith(parameter_prefix):
            if parameter_found:
                msg = f"Multiple {parameter_name} parameters found in connection string"
                raise ValueError(msg)

            parameter_found = True
            # Extract the value after the equals sign
            parameter_value = part.split("=", 1)[1].strip()

        elif part == parameter_name:
            # Parameter without equals sign
            msg = f"Malformed {parameter_name} parameter: missing equals sign"
            raise ValueError(msg)
        elif part.lower().startswith(parameter_name.lower() + "=") and not part.startswith(parameter_prefix):
            # Case sensitivity issue
            msg = f"{parameter_name} parameter must use exact case '{parameter_prefix}' (found: '{part.split('=')[0]}=')"
            raise ValueError(msg)

    if not parameter_found:
        msg = f"{parameter_name} parameter not found in connection string"
        raise ValueError(msg)

    if parameter_value == "":
        msg = f"{parameter_name} parameter cannot be empty"
        raise ValueError(msg)

    return parameter_value


def _extract_account_name_from_connection_string(
    connection_string: str
    ) -> str:
    """Extract the account name from an Azure Storage connection string.

    Parameters
    ----------
    connection_string : str
        The Azure Storage connection string.

    Returns
    -------
    str
        The account name extracted from the connection string.
    """
    return _extract_parameter_from_connection_string(connection_string, "AccountName")


def _extract_account_key_from_connection_string(
    connection_string: str
    ) -> str:
    """Extract the account key from an Azure Storage connection string.

    Parameters
    ----------
    connection_string : str
        The Azure Storage connection string.

    Returns
    -------
    str
        The account key extracted from the connection string.
    """
    return _extract_parameter_from_connection_string(connection_string, "AccountKey")


def validate_azure_storage_config(
    connection_string: str,
) -> dict:
    """Validate an Azure Storage configuration.

    Parameters
    ----------
    connection_string : str
        The Azure Storage connection string.

    Returns
    -------
    dict
        Validation results with status and details. Contains:
        - 'valid': bool indicating if configuration is valid
        - 'error': str with error message if invalid, None if valid
    """
    if not connection_string:
        msg = "An Azure Storage connection string is required"
        raise ValueError(msg)

    try:
        acc_nm = _extract_account_name_from_connection_string(connection_string)
        key = _extract_account_key_from_connection_string(connection_string)
    except ValueError as e:
        return {
            "valid": False,
            "error": f"Connection string validation failed: {e!s}"
        }

    try:
        # Validate the key
        is_valid = _validate_azure_account_key(acc_nm, key)
    except Exception as e:
        return {
            "valid": False,
            "error": f"Azure config validation failed: {e!s}",
        }
    else:
        return {
            "valid": is_valid,
            "error": None if is_valid else "Account key is invalid"
        }


# =============================================================================
# Blob Management Functions
# =============================================================================

class AzureBlobManager:
    """Manages Azure Blob Storage operations for audio files.

    This class provides both synchronous and asynchronous methods for
    creating, deleting, and checking the existence of blobs in Azure Storage.
    """

    def __init__(self, connection_string: str | None = None):
        """Initialize the blob manager with connection string.

        Parameters
        ----------
        connection_string : str, optional
            Azure Storage connection string. If None, uses settings from
            get_settings().AZURE_STORAGE_CONNECTION_STRING.
        """
        self.connection_string = connection_string or get_settings().AZURE_STORAGE_CONNECTION_STRING
        self.account_name = get_settings().AZURE_STORAGE_ACCOUNT_NAME
        self.container_name = get_settings().AZURE_STORAGE_CONTAINER_NAME

    def create_blob_from_file(self, file_path: Path, blob_name: str,
                             container_name: str | None = None) -> bool:
        """Create a blob from a local file.

        Parameters
        ----------
        file_path : Path
            Path to the local file to upload.
        blob_name : str
            Name of the blob in Azure Storage.
        container_name : str, optional
            Container name. If None, uses the default container from settings.

        Returns
        -------
        bool
            True if successful, False otherwise.
        """
        try:
            container = container_name or self.container_name

            # Create BlobClient
            blob_client = BlobClient.from_connection_string(
                conn_str=self.connection_string,
                container_name=container,
                blob_name=blob_name
            )

            # Upload the file
            with file_path.open("rb") as data:
                blob_client.upload_blob(data, overwrite=True)

            logger.info(f"Successfully created blob: {container}/{blob_name}")
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return False
        except ResourceExistsError:
            logger.warning(f"Blob already exists: {container}/{blob_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to create blob {container}/{blob_name}: {e}")
            return False
        else:
            return True

    def delete_blob(self, blob_name: str, container_name: str | None = None,
                   delete_snapshots: str = "include") -> bool:
        """Delete a blob from Azure Storage.

        Parameters
        ----------
        blob_name : str
            Name of the blob to delete.
        container_name : str, optional
            Container name. If None, uses the default container from settings.
        delete_snapshots : str, optional
            How to handle snapshots. Options: "include", "only", None.
            Default is "include".

        Returns
        -------
        bool
            True if successful, False otherwise.
        """
        try:
            container = container_name or self.container_name

            # Create BlobClient
            blob_client = BlobClient.from_connection_string(
                conn_str=self.connection_string,
                container_name=container,
                blob_name=blob_name
            )

            # Delete the blob
            blob_client.delete_blob(delete_snapshots=delete_snapshots)

            logger.info(f"Successfully deleted blob: {container}/{blob_name}")
        except ResourceNotFoundError:
            logger.warning(f"Blob not found: {container}/{blob_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete blob {container}/{blob_name}: {e}")
            return False
        else:
            return True

    def blob_exists(self, blob_name: str, container_name: str | None = None) -> bool:
        """Check if a blob exists in Azure Storage.

        Parameters
        ----------
        blob_name : str
            Name of the blob to check.
        container_name : str, optional
            Container name. If None, uses the default container from settings.

        Returns
        -------
        bool
            True if blob exists, False otherwise.
        """
        try:
            container = container_name or self.container_name

            # Create BlobClient
            blob_client = BlobClient.from_connection_string(
                conn_str=self.connection_string,
                container_name=container,
                blob_name=blob_name
            )

            # Check if blob exists
            return blob_client.exists()

        except Exception as e:
            logger.error(f"Failed to check if blob exists {container}/{blob_name}: {e}")
            return False


class AsyncAzureBlobManager:
    """Async version of Azure Blob Storage manager.

    This class provides asynchronous methods for creating, deleting, and
    checking the existence of blobs in Azure Storage.
    """

    def __init__(self, connection_string: str | None = None):
        """Initialize the async blob manager with connection string.

        Parameters
        ----------
        connection_string : str, optional
            Azure Storage connection string. If None, uses settings from
            get_settings().AZURE_STORAGE_CONNECTION_STRING.
        """
        self.connection_string = connection_string or get_settings().AZURE_STORAGE_CONNECTION_STRING
        self.account_name = get_settings().AZURE_STORAGE_ACCOUNT_NAME
        self.container_name = get_settings().AZURE_STORAGE_CONTAINER_NAME

    async def create_blob_from_file(self, file_path: Path, blob_name: str,
                                  container_name: str | None = None) -> bool:
        """Create a blob from a local file (async).

        Parameters
        ----------
        file_path : Path
            Path to the local file to upload.
        blob_name : str
            Name of the blob in Azure Storage.
        container_name : str, optional
            Container name. If None, uses the default container from settings.

        Returns
        -------
        bool
            True if successful, False otherwise.
        """
        try:
            container = container_name or self.container_name

            # Create async BlobServiceClient
            async with AsyncBlobServiceClient.from_connection_string(self.connection_string) as blob_service_client:
                blob_client = blob_service_client.get_blob_client(
                    container=container,
                    blob=blob_name
                )

                # Upload the file
                with file_path.open("rb") as data:
                    await blob_client.upload_blob(data, overwrite=True)

            logger.info(f"Successfully created blob: {container}/{blob_name}")
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return False
        except ResourceExistsError:
            logger.warning(f"Blob already exists: {container}/{blob_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to create blob {container}/{blob_name}: {e}")
            return False
        else:
            return True

    async def delete_blob(self, blob_name: str, container_name: str | None = None,
                         delete_snapshots: str = "include") -> bool:
        """Delete a blob from Azure Storage (async).

        Parameters
        ----------
        blob_name : str
            Name of the blob to delete.
        container_name : str, optional
            Container name. If None, uses the default container from settings.
        delete_snapshots : str, optional
            How to handle snapshots. Options: "include", "only", None.
            Default is "include".

        Returns
        -------
        bool
            True if successful, False otherwise.
        """
        try:
            container = container_name or self.container_name

            # Create async BlobServiceClient
            async with AsyncBlobServiceClient.from_connection_string(self.connection_string) as blob_service_client:
                blob_client = blob_service_client.get_blob_client(
                    container=container,
                    blob=blob_name
                )

                # Delete the blob
                await blob_client.delete_blob(delete_snapshots=delete_snapshots)

            logger.info(f"Successfully deleted blob: {container}/{blob_name}")
        except ResourceNotFoundError:
            logger.warning(f"Blob not found: {container}/{blob_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete blob {container}/{blob_name}: {e}")
            return False
        else:
            return True

    async def blob_exists(self, blob_name: str, container_name: str | None = None) -> bool:
        """Check if a blob exists in Azure Storage (async).

        Parameters
        ----------
        blob_name : str
            Name of the blob to check.
        container_name : str, optional
            Container name. If None, uses the default container from settings.

        Returns
        -------
        bool
            True if blob exists, False otherwise.
        """
        try:
            container = container_name or self.container_name

            # Create async BlobServiceClient
            async with AsyncBlobServiceClient.from_connection_string(self.connection_string) as blob_service_client:
                blob_client = blob_service_client.get_blob_client(
                    container=container,
                    blob=blob_name
                )

                # Check if blob exists
                return await blob_client.exists()

        except Exception as e:
            logger.error(f"Failed to check if blob exists {container}/{blob_name}: {e}")
            return False


