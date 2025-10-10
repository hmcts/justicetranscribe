"""Deduplicate allowlist in Azure Blob Storage (case-insensitive).

This script:
1. Downloads the current allowlist from Azure
2. Removes duplicate emails (case-insensitive, keeps first occurrence)
3. Uploads the deduplicated list back to Azure

Usage:
    python deduplicate_allowlist.py --env dev
    python deduplicate_allowlist.py --env prod
"""
import argparse
import sys
from io import StringIO
import pandas as pd
from azure.storage.blob import BlobServiceClient
from dotenv import dotenv_values


def download_allowlist(connection_string: str, container: str, blob_path: str) -> pd.DataFrame:
    """Download allowlist from Azure Blob Storage.
    
    Returns:
        DataFrame with email and provider columns
    """
    service = BlobServiceClient.from_connection_string(connection_string)
    blob_client = service.get_blob_client(container=container, blob=blob_path)
    
    # Download blob content as string
    download_stream = blob_client.download_blob()
    content = download_stream.readall().decode("utf-8")
    
    # Parse CSV with pandas
    df_with_header = pd.read_csv(StringIO(content))
    
    # Check if it has the right columns (has header row)
    if 'email' in df_with_header.columns and 'provider' in df_with_header.columns:
        df = df_with_header
    else:
        # No headers, read again without headers
        df = pd.read_csv(StringIO(content), names=["email", "provider"])
    
    print(f"📥 Downloaded allowlist: {len(df)} rows")
    return df


def upload_allowlist(connection_string: str, container: str, blob_path: str, df: pd.DataFrame) -> None:
    """Upload allowlist DataFrame to Azure Blob Storage with headers."""
    service = BlobServiceClient.from_connection_string(connection_string)
    
    # Convert DataFrame to CSV string (with headers)
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, header=True, encoding="utf-8")
    csv_bytes = csv_buffer.getvalue().encode("utf-8")
    
    # Upload
    blob_client = service.get_blob_client(container=container, blob=blob_path)
    blob_client.upload_blob(csv_bytes, overwrite=True, content_type="text/csv; charset=utf-8")
    
    print(f"✅ Uploaded deduplicated allowlist: {len(df)} rows")


def deduplicate_allowlist(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Remove duplicate emails (case-insensitive).
    
    Args:
        df: DataFrame with email and provider columns
        
    Returns:
        Tuple of (deduplicated_df, stats_dict)
    """
    original_count = len(df)
    
    # Create a lowercase email column for comparison
    df['email_lower'] = df['email'].str.lower().str.strip()
    
    # Find duplicates before removing them
    duplicates = df[df.duplicated(subset=['email_lower'], keep=False)]
    duplicate_emails = duplicates['email_lower'].unique()
    
    # Remove duplicates (keep first occurrence)
    deduplicated = df.drop_duplicates(subset=['email_lower'], keep='first').copy()
    
    # Remove the temporary lowercase column
    deduplicated = deduplicated.drop(columns=['email_lower'])
    
    # Reset index
    deduplicated = deduplicated.reset_index(drop=True)
    
    duplicates_removed = original_count - len(deduplicated)
    
    stats = {
        'original_count': original_count,
        'final_count': len(deduplicated),
        'duplicates_removed': duplicates_removed,
        'duplicate_emails': sorted(duplicate_emails) if duplicates_removed > 0 else []
    }
    
    return deduplicated, stats


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Deduplicate allowlist in Azure Blob Storage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Deduplicate dev allowlist
    python deduplicate_allowlist.py --env dev
    
    # Deduplicate prod allowlist
    python deduplicate_allowlist.py --env prod
        """
    )
    
    parser.add_argument(
        "--env",
        choices=["dev", "prod"],
        required=True,
        help="Target environment (dev or prod)"
    )
    
    args = parser.parse_args()
    
    try:
        print(f"🚀 Deduplicating {args.env.upper()} allowlist...")
        print()
        
        # Load environment variables
        secrets = dotenv_values()
        container = secrets.get("AZURE_STORAGE_CONTAINER_NAME")
        
        if not container:
            raise ValueError("AZURE_STORAGE_CONTAINER_NAME not found in .env file")
        
        if args.env == "dev":
            connection_string = secrets.get("AZURE_STORAGE_CONNECTION_STRING")
        else:  # prod
            connection_string = secrets.get("AZURE_STORAGE_CONNECTION_STRING_PROD")
        
        if not connection_string:
            raise ValueError(f"Connection string for {args.env} not found in .env file")
        
        blob_path = "lookups/allowlist.csv"
        
        # Step 1: Download current allowlist
        df = download_allowlist(connection_string, container, blob_path)
        
        # Step 2: Deduplicate
        print()
        print("🔄 Checking for duplicates...")
        deduplicated_df, stats = deduplicate_allowlist(df)
        
        # Step 3: Show results
        print()
        print("📊 Deduplication Results:")
        print(f"   Original rows: {stats['original_count']}")
        print(f"   Final rows: {stats['final_count']}")
        print(f"   Duplicates removed: {stats['duplicates_removed']}")
        
        if stats['duplicates_removed'] > 0:
            print()
            print("   Duplicate emails found (kept first occurrence):")
            for email in stats['duplicate_emails']:
                print(f"      - {email}")
        else:
            print()
            print("   ✅ No duplicates found!")
        
        # Step 4: Upload
        if stats['duplicates_removed'] > 0:
            print()
            print(f"📤 Uploading deduplicated allowlist to {args.env.upper()}...")
            upload_allowlist(connection_string, container, blob_path, deduplicated_df)
            print()
            print(f"✅ Success! {args.env.upper()} allowlist deduplicated")
        else:
            print()
            print("✅ No duplicates found - no changes needed")
        
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

