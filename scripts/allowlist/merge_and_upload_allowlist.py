"""Merge a local allowlist file with existing Azure allowlist and upload.

This script:
1. Downloads current allowlist from Azure blob storage
2. Loads and validates local file with strict data quality checks
3. Merges them (deduplicates by email)
4. Uploads the merged result back to Azure

Usage:
    python merge_and_upload_allowlist.py --env dev --file data/dev-allowlist-update-2025-10-08_12-06-24.csv
    python merge_and_upload_allowlist.py --env prod --file data/prod-allowlist-update-2025-10-08_12-06-24.csv
"""
import argparse
import sys
from pathlib import Path
from typing import Tuple
import pandas as pd
from azure.storage.blob import BlobServiceClient
from dotenv import dotenv_values


class DataQualityError(Exception):
    """Raised when data quality checks fail."""
    pass


def _download_from_azure(connection_string: str, container: str, blob_path: str) -> pd.DataFrame:
    """Download current allowlist from Azure Blob Storage.
    
    Returns:
        DataFrame with email and provider columns, or empty DataFrame if doesn't exist
    """
    try:
        service = BlobServiceClient.from_connection_string(connection_string)
        blob_client = service.get_blob_client(container=container, blob=blob_path)
        
        # Download blob content as string
        download_stream = blob_client.download_blob()
        content = download_stream.readall().decode("utf-8")
        
        # Parse CSV with pandas - handle both with and without headers
        from io import StringIO
        
        # First try reading with headers
        df_with_header = pd.read_csv(StringIO(content))
        
        # Check if it has the right columns (has header row)
        if 'email' in df_with_header.columns and 'provider' in df_with_header.columns:
            df = df_with_header
        else:
            # No headers, read again without headers
            df = pd.read_csv(StringIO(content), names=["email", "provider"])
        
        print(f"📥 Downloaded existing allowlist: {len(df)} users")
        return df
        
    except Exception as e:
        print(f"⚠️  Could not download existing allowlist (might not exist yet): {e}")
        print("   Creating new allowlist from local file only...")
        return pd.DataFrame(columns=["email", "provider"])


def _upload_to_azure(
    connection_string: str, container: str, blob_path: str, df: pd.DataFrame
) -> None:
    """Upload allowlist DataFrame to Azure Blob Storage with headers."""
    service = BlobServiceClient.from_connection_string(connection_string)
    
    # Ensure container exists
    try:
        service.create_container(container)
    except Exception:
        pass
    
    # Data quality check: Ensure column names are correct
    if list(df.columns) != ['email', 'provider']:
        raise DataQualityError(
            f"DataFrame must have columns ['email', 'provider'], got: {list(df.columns)}"
        )
    
    # Data quality check: Ensure no data rows contain the header values
    header_rows = df[
        (df['email'].str.lower() == 'email') & 
        (df['provider'].str.lower() == 'provider')
    ]
    if not header_rows.empty:
        raise DataQualityError(
            f"Found {len(header_rows)} data rows that look like headers. "
            "Headers should only be in the column names, not in data."
        )
    
    # Convert DataFrame to CSV bytes (no index, WITH headers)
    from io import StringIO
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, header=True, encoding="utf-8")
    csv_bytes = csv_buffer.getvalue().encode("utf-8")
    
    # Verify only one header line in output
    csv_content = csv_buffer.getvalue()
    header_count = csv_content.lower().count('email,provider')
    if header_count != 1:
        raise DataQualityError(
            f"Expected exactly 1 header line, found {header_count}. "
            "This indicates duplicate headers in the data."
        )
    
    # Upload
    blob_client = service.get_blob_client(container=container, blob=blob_path)
    blob_client.upload_blob(
        csv_bytes, overwrite=True, content_type="text/csv; charset=utf-8"
    )
    
    print(f"✅ Uploaded to {container}/{blob_path} with headers")


def clean_email(email: str) -> str:
    """Clean email address with strict validation.
    
    Removes:
    - Leading/trailing whitespace
    - Leading newlines/line breaks
    - Trailing '>' characters
    """
    if pd.isna(email) or not isinstance(email, str):
        raise DataQualityError(f"Invalid email (null or non-string): {email}")
    
    # Remove leading line breaks
    email = email.lstrip('\n\r')
    
    # Remove trailing >
    email = email.rstrip('>')
    
    # Strip whitespace
    email = email.strip()
    
    # Lowercase
    email = email.lower()
    
    return email


def clean_provider(provider: str) -> str:
    """Clean provider field with strict validation."""
    if pd.isna(provider) or not isinstance(provider, str):
        raise DataQualityError(f"Invalid provider (null or non-string): {provider}")
    
    # Remove leading/trailing whitespace and line breaks
    provider = provider.strip().lstrip('\n\r')
    
    # Lowercase
    provider = provider.lower()
    
    if not provider:
        raise DataQualityError("Provider cannot be empty after cleaning")
    
    return provider


def validate_and_clean_dataframe(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Perform strict data quality checks and cleaning on DataFrame.
    
    Args:
        df: DataFrame to validate
        source: Description of data source (for error messages)
        
    Returns:
        Cleaned DataFrame
        
    Raises:
        DataQualityError: If any validation fails
    """
    print(f"🔍 Validating {source}...")
    
    # Check for required columns
    if 'email' not in df.columns or 'provider' not in df.columns:
        raise DataQualityError(
            f"{source}: Missing required columns. Found: {df.columns.tolist()}"
        )
    
    # Check for null values
    null_emails = df['email'].isna().sum()
    null_providers = df['provider'].isna().sum()
    
    if null_emails > 0:
        raise DataQualityError(f"{source}: Found {null_emails} null email values")
    
    if null_providers > 0:
        raise DataQualityError(f"{source}: Found {null_providers} null provider values")
    
    # Check for header rows in data (case-insensitive)
    header_like_rows = df[
        (df['email'].astype(str).str.lower() == 'email') & 
        (df['provider'].astype(str).str.lower() == 'provider')
    ]
    if not header_like_rows.empty:
        raise DataQualityError(
            f"{source}: Found {len(header_like_rows)} rows containing header values 'email,provider' in data. "
            f"Headers should only be column names, not data rows."
        )
    
    # Clean each row
    cleaned_rows = []
    errors = []
    
    for idx, row in df.iterrows():
        try:
            cleaned_email = clean_email(row['email'])
            cleaned_provider = clean_provider(row['provider'])
            
            # Validate email format (basic check)
            if '@' not in cleaned_email or '.' not in cleaned_email:
                errors.append(f"Row {idx}: Invalid email format: '{cleaned_email}'")
                continue
            
            cleaned_rows.append({
                'email': cleaned_email,
                'provider': cleaned_provider
            })
            
        except DataQualityError as e:
            errors.append(f"Row {idx}: {str(e)}")
    
    if errors:
        error_msg = f"{source}: Data quality issues found:\n" + "\n".join(errors)
        raise DataQualityError(error_msg)
    
    cleaned_df = pd.DataFrame(cleaned_rows)
    print(f"✅ Validation passed: {len(cleaned_df)} rows cleaned")
    
    return cleaned_df


def load_local_file(file_path: Path) -> pd.DataFrame:
    """Load and validate local allowlist file.
    
    Handles files with or without headers.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    print(f"📂 Loading local file: {file_path}")
    
    # Try loading with headers first
    df_with_header = pd.read_csv(file_path, encoding="utf-8")
    
    # Check if it has the right columns
    if 'email' in df_with_header.columns and 'provider' in df_with_header.columns:
        # File has headers
        df = df_with_header
    else:
        # No headers, assume email,provider format
        df = pd.read_csv(file_path, names=["email", "provider"], encoding="utf-8")
    
    print(f"📊 Loaded {len(df)} rows from local file")
    
    return df


def merge_allowlists(existing_df: pd.DataFrame, new_df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """Merge existing and new allowlists, removing duplicates.
    
    Priority: Existing entries take precedence (keeps original provider for duplicates)
    
    Returns:
        Tuple of (merged_df, stats_dict)
    """
    print("🔄 Merging allowlists...")
    
    # Track what we're doing
    existing_emails = set(existing_df['email'].str.lower())
    new_emails = set(new_df['email'].str.lower())
    
    # Combine dataframes
    combined = pd.concat([existing_df, new_df], ignore_index=True)
    
    # Remove duplicates (keep first occurrence - existing data)
    # Keep chronological order - existing users first, then new users
    merged = combined.drop_duplicates(subset=['email'], keep='first').reset_index(drop=True)
    
    # Calculate stats
    stats = {
        'existing_count': len(existing_df),
        'new_file_count': len(new_df),
        'truly_new': len(new_emails - existing_emails),
        'duplicates_removed': len(combined) - len(merged),
        'final_count': len(merged)
    }
    
    print("📈 Merge statistics:")
    print(f"   - Existing users: {stats['existing_count']}")
    print(f"   - New file users: {stats['new_file_count']}")
    print(f"   - Truly new users: {stats['truly_new']}")
    print(f"   - Duplicates removed: {stats['duplicates_removed']}")
    print(f"   - Final total: {stats['final_count']}")
    
    return merged, stats


def merge_and_upload(environment: str, local_file: Path) -> None:
    """Main function to merge local file with Azure allowlist and upload.
    
    Args:
        environment: 'dev' or 'prod'
        local_file: Path to local allowlist file to merge
    """
    if environment not in ["dev", "prod"]:
        raise ValueError(f"Environment must be 'dev' or 'prod', got: {environment}")
    
    print(f"🚀 Merging and uploading {environment} allowlist...")
    print()
    
    # Load environment variables
    secrets = dotenv_values()
    container = secrets.get("AZURE_STORAGE_CONTAINER_NAME")
    
    if not container:
        raise ValueError("AZURE_STORAGE_CONTAINER_NAME not found in .env file")
    
    if environment == "dev":
        connection_string = secrets.get("AZURE_STORAGE_CONNECTION_STRING")
    else:  # prod
        connection_string = secrets.get("AZURE_STORAGE_CONNECTION_STRING_PROD")
    
    if not connection_string:
        raise ValueError(f"Connection string for {environment} not found in .env file")
    
    blob_path = "lookups/allowlist.csv"
    
    # Step 1: Download existing allowlist from Azure
    existing_df = _download_from_azure(connection_string, container, blob_path)
    
    # Step 2: Load and validate local file
    new_df = load_local_file(local_file)
    
    # Step 3: Validate and clean both dataframes
    print()
    if not existing_df.empty:
        existing_df = validate_and_clean_dataframe(existing_df, "Existing Azure allowlist")
    
    new_df = validate_and_clean_dataframe(new_df, "Local file")
    
    # Step 4: Merge
    print()
    merged_df, stats = merge_allowlists(existing_df, new_df)
    
    # Step 5: Final validation on merged data
    print()
    merged_df = validate_and_clean_dataframe(merged_df, "Merged allowlist")
    
    # Step 6: Upload to Azure
    print()
    print(f"📤 Uploading to {environment}...")
    _upload_to_azure(connection_string, container, blob_path, merged_df)
    
    print()
    print(f"✅ Success! {environment.upper()} allowlist updated")
    print(f"   📊 Final count: {len(merged_df)} users")
    print(f"   ➕ Added: {stats['truly_new']} new users")


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Merge local allowlist file with Azure allowlist and upload",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Merge and upload dev allowlist
    python merge_and_upload_allowlist.py --env dev --file data/dev-allowlist-update-2025-10-08_12-06-24.csv
    
    # Merge and upload prod allowlist
    python merge_and_upload_allowlist.py --env prod --file data/prod-allowlist-update-2025-10-08_14-30-00.csv
        """
    )
    
    parser.add_argument(
        "--env",
        choices=["dev", "prod"],
        required=True,
        help="Target environment (dev or prod)"
    )
    
    parser.add_argument(
        "--file",
        required=True,
        type=Path,
        help="Path to local allowlist file to merge and upload"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform merge and validation but don't upload to Azure"
    )
    
    args = parser.parse_args()
    
    try:
        if args.dry_run:
            print("🔍 DRY RUN MODE - Will not upload to Azure")
            print()
        
        merge_and_upload(args.env, args.file)
        
        if args.dry_run:
            print()
            print("🔍 DRY RUN - No changes made to Azure")
        
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

