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
    


def _extract_parameter_from_connection_string(
    connection_string: str, 
    parameter_name: str
    ) -> str:
    """
    Extract a parameter value from an Azure Storage connection string.
    
    Args:
        connection_string: The Azure Storage connection string
        parameter_name: The parameter name to extract (e.g., 'AccountName', 'AccountKey')
        
    Returns:
        str: The parameter value extracted from the connection string
        
    Raises:
        ValueError: If the connection string is empty, malformed, or missing the parameter
    """
    if not connection_string:
        raise ValueError("Connection string cannot be empty")
    
    if not connection_string.strip():
        raise ValueError("Connection string cannot be whitespace only")
    
    # Split by semicolon and look for the specified parameter
    parameter_found = False
    parameter_value = None
    parameter_prefix = f"{parameter_name}="
    
    for part in connection_string.split(";"):
        part = part.strip()  # Remove leading/trailing whitespace from each part
        
        if part.startswith(parameter_prefix):
            if parameter_found:
                raise ValueError(f"Multiple {parameter_name} parameters found in connection string")
            
            parameter_found = True
            # Extract the value after the equals sign
            parameter_value = part.split("=", 1)[1].strip()
            
        elif part == parameter_name:
            # Parameter without equals sign
            raise ValueError(f"Malformed {parameter_name} parameter: missing equals sign")
        elif part.lower().startswith(parameter_name.lower() + "=") and not part.startswith(parameter_prefix):
            # Case sensitivity issue
            raise ValueError(f"{parameter_name} parameter must use exact case '{parameter_prefix}' (found: '{part.split('=')[0]}=')")
    
    if not parameter_found:
        raise ValueError(f"{parameter_name} parameter not found in connection string")
    
    if parameter_value == "":
        raise ValueError(f"{parameter_name} parameter cannot be empty")
    
    return parameter_value


def _extract_account_name_from_connection_string(
    connection_string: str
    ) -> str:
    """Extract the account name from an Azure Storage connection string."""
    return _extract_parameter_from_connection_string(connection_string, "AccountName")


def _extract_account_key_from_connection_string(
    connection_string: str
    ) -> str:
    """Extract the account key from an Azure Storage connection string."""
    return _extract_parameter_from_connection_string(connection_string, "AccountKey")


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
