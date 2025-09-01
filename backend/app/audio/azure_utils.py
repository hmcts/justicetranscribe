"""Azure Storage utilities that don't depend on application settings."""

from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ClientAuthenticationError


def _validate_azure_account_key(account_name: str, account_key: str, conn_timeout: int = 5) -> bool:
    """Validate that the Azure Storage account key is current and active."""
    
    try:

        # Create a BlobServiceClient with the account name and key
        blob_service_client = BlobServiceClient(
            account_url=f"https://{account_name}.blob.core.windows.net",
            credential=account_key,
            connection_timeout=conn_timeout,
        )
        
        # Attempt a simple operation requiring auth
        containers = list(
            blob_service_client.list_containers(timeout=conn_timeout)
            )
        return True

    except ClientAuthenticationError as e:
        # Case where account name is found but key is invalid
        return False

    except Exception as e:
        raise Exception(
            f"Account key for account {account_name} is invalid: {str(e)}"
            )
    


def _extract_account_name_from_connection_string(
    connection_string: str
    ) -> str | None:
    """Extract the account name from an Azure Storage connection string."""
    for part in connection_string.split(";"):
        if part.startswith("AccountName="):
            return part.split("=", 1)[1]
    return None


def _extract_account_key_from_connection_string(
    connection_string: str
    ) -> str | None:
    """Extract the account key from an Azure Storage connection string."""
    for part in connection_string.split(";"):
        if part.startswith("AccountKey="):
            return part.split("=", 1)[1]
    return None


def validate_azure_storage_config(
    connection_string: str, 
) -> dict:
    """Validate an Azure Storage configuration.
    
    Args:
        account_name (str): The Azure Storage account name
        connection_string (str): The Azure Storage connection string
        container_name (str): The container name
        
    Returns:
        dict: Validation results with status and details
    """
    if not connection_string:
        raise ValueError("An Azure Storage connection string is required")
    acc_nm = _extract_account_name_from_connection_string(connection_string)
    key = _extract_account_key_from_connection_string(connection_string)


    if not acc_nm or not key:
        return {
            "valid": False,
            "error": "Couldn't extract account name or key from Azure Storage connection string.",
            "account_name": acc_nm
        }

    try:
        # Validate the key
        is_valid = _validate_azure_account_key(acc_nm, key)
        
        return {
            "valid": is_valid,
            "error": None if is_valid else "Account key is invalid"
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error": f"Azure config validation failed: {str(e)}",
        }
