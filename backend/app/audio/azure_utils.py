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
    ) -> str:
    """Extract the account name from an Azure Storage connection string."""
    if not connection_string:
        raise ValueError("Connection string cannot be empty")
    
    if not connection_string.strip():
        raise ValueError("Connection string cannot be whitespace only")
    
    # Split by semicolon and look for AccountName parameter
    account_name_found = False
    account_name_value = None
    
    for part in connection_string.split(";"):
        part = part.strip()  # Remove leading/trailing whitespace from each part
        
        if part.startswith("AccountName="):
            if account_name_found:
                raise ValueError("Multiple AccountName parameters found in connection string")
            
            account_name_found = True
            # Extract the value after the equals sign
            if "=" not in part:
                raise ValueError("Malformed AccountName parameter: missing equals sign")
            
            account_name_value = part.split("=", 1)[1].strip()
            
        elif part == "AccountName":
            # AccountName without equals sign
            raise ValueError("Malformed AccountName parameter: missing equals sign")
        elif part.lower().startswith("accountname=") and not part.startswith("AccountName="):
            # Case sensitivity issue
            raise ValueError("AccountName parameter must use exact case 'AccountName=' (found: '{}')".format(part.split("=")[0] + "="))
    
    if not account_name_found:
        raise ValueError("AccountName parameter not found in connection string")
    
    if account_name_value == "":
        raise ValueError("AccountName parameter cannot be empty")
    
    return account_name_value


def _extract_account_key_from_connection_string(
    connection_string: str
    ) -> str:
    """Extract the account key from an Azure Storage connection string."""
    if not connection_string:
        raise ValueError("Connection string cannot be empty")
    
    if not connection_string.strip():
        raise ValueError("Connection string cannot be whitespace only")
    
    # Split by semicolon and look for AccountKey parameter
    account_key_found = False
    account_key_value = None
    
    for part in connection_string.split(";"):
        part = part.strip()  # Remove leading/trailing whitespace from each part
        
        if part.startswith("AccountKey="):
            if account_key_found:
                raise ValueError("Multiple AccountKey parameters found in connection string")
            
            account_key_found = True
            # Extract the value after the equals sign
            if "=" not in part:
                raise ValueError("Malformed AccountKey parameter: missing equals sign")
            
            account_key_value = part.split("=", 1)[1].strip()
            
        elif part == "AccountKey":
            # AccountKey without equals sign
            raise ValueError("Malformed AccountKey parameter: missing equals sign")
        elif part.lower().startswith("accountkey=") and not part.startswith("AccountKey="):
            # Case sensitivity issue
            raise ValueError("AccountKey parameter must use exact case 'AccountKey=' (found: '{}')".format(part.split("=")[0] + "="))
    
    if not account_key_found:
        raise ValueError("AccountKey parameter not found in connection string")
    
    if account_key_value == "":
        raise ValueError("AccountKey parameter cannot be empty")
    
    return account_key_value


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
    
    try:
        acc_nm = _extract_account_name_from_connection_string(connection_string)
        key = _extract_account_key_from_connection_string(connection_string)
    except ValueError as e:
        return {
            "valid": False,
            "error": f"Connection string validation failed: {str(e)}"
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
