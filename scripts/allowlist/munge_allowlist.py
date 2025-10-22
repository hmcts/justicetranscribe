"""A script to ingest allowlist csv, prep and save to blob storage.
Data dependencies:
* data/pilot_users.csv
Output:
* data/allowlist_final.csv (prod allowlist)
* data/allowlist_dev.csv (dev allowlist)
Usage:
    python munge_allowlist.py --env dev|prod|both
"""

import argparse
from pathlib import Path
from azure.storage.blob import BlobServiceClient
from dotenv import dotenv_values
import pandas as pd
from pyprojroot import here


def _upload_with_connection_string(
    connection_string: str, container: str, blob_path: str, file_path: Path
) -> None:
    """Upload a file to Azure Blob Storage."""
    service = BlobServiceClient.from_connection_string(connection_string)
    try:
        service.create_container(container)
    except Exception:
        pass
    blob_client = service.get_blob_client(container=container, blob=blob_path)
    with open(file_path, "rb") as fh:
        blob_client.upload_blob(
            fh, overwrite=True, content_type="text/csv; charset=utf-8"
        )
    print(f"✅ Uploaded {file_path} to {container}/{blob_path}")


def _load_ai_justice_unit_data() -> pd.DataFrame:
    """Load AI Justice Unit team data."""
    ai_justice_unit = pd.DataFrame(
        {
            "email": [
                "ayse.mutlu@justice.gov.uk",
                "dan.james@justice.gov.uk",
                "developer@localhost.com",
                "franziska.hasford@justice.gov.uk",
                "john.daley@justice.gov.uk",
                "louis.allgood@justice.gov.uk",
                "richard.leyshon@justice.gov.uk",
                "sam.lhuillier@justice.gov.uk",
            ],
        }
    )
    ai_justice_unit["provider"] = "ai justice unit"
    return ai_justice_unit


def _load_pilot_data() -> pd.DataFrame:
    """Load pilot users data from CSV."""
    pilot_pth = here("data/pilot_users.csv")
    pilot_df = pd.read_csv(pilot_pth, encoding="cp1252", names=["email", "provider"])
    # Remove trailing > characters that sometimes appear in malformed emails
    pilot_df["email"] = pilot_df["email"].str.rstrip(">")
    return pilot_df


def _load_manually_onboarded_data() -> pd.DataFrame:
    """Load manually onboarded users data."""
    manually_onboarded = pd.DataFrame.from_records(
        [
            ("adele.alenizy@justice.gov.uk", "wales"),
            ("clare.phillips@justice.gov.uk", "wales"),
            ("carys.girvin@justice.gov.uk", "hq-dpm"),
            ("helen.smith11@justice.gov.uk", "wales"),
            ("jessamine.stonehouse@justice.gov.uk", "hq-dpm"),
            ("katie.morris2@justice.gov.uk", "hq-dpm"),
            ("louis.clarke@justice.gov.uk", "hq-dpm"),
            ("louisa.chatterton@justice.gov.uk", "hq-dpm"),
            ("michael.arnold@justice.gov.uk", "hmppg"),
            ("sam.denman@justice.gov.uk", "hq"),
            ("samantha.merrett@justice.gov.uk", "hq-dat"),
            ("matt.proctor-leake@justice.gov.uk", "hq-dat"),
            ("minaz.ali@justice.gov.uk", "kss"),
        ],
        columns=["email", "provider"],
    )
    return manually_onboarded


def _normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize dataframe by lowercasing and stripping all string columns."""
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: x.lower().strip() if isinstance(x, str) else x
        )
    return df


def create_allowlist(environment: str) -> Path:
    """Create an allowlist for the specified environment.

    Args:
        environment: Either 'dev' or 'prod'

    Returns:
        Path to the created allowlist file
    """
    if environment not in ["dev", "prod"]:
        raise ValueError(f"Environment must be 'dev' or 'prod', got: {environment}")

    print(f"🔄 Creating {environment} allowlist...")

    # Load all data sources
    ai_justice_unit = _load_ai_justice_unit_data()
    pilot_df = _load_pilot_data()
    manually_onboarded = _load_manually_onboarded_data()

    # Combine all data
    out_df = pd.concat(
        [pilot_df, ai_justice_unit, manually_onboarded], ignore_index=True
    )

    # Normalize data (lowercase, strip whitespace)
    out_df = _normalize_dataframe(out_df)

    # Drop duplicates AFTER normalization to catch case-insensitive duplicates
    out_df = out_df.drop_duplicates(subset=["email"], keep="first").reset_index(
        drop=True
    )

    # Filter data based on environment
    if environment == "dev":
        # Dev allowlist contains only AI Justice Unit team
        filtered_df = out_df.query("provider == 'ai justice unit'").reset_index(
            drop=True
        )
        output_path = here("data/allowlist_dev.csv")
    else:  # prod
        # Prod allowlist contains all users
        filtered_df = out_df
        output_path = here("data/allowlist_final.csv")

    # Save to file
    filtered_df.to_csv(output_path, index=False, encoding="utf-8")

    print(f"✅ {environment.title()} allowlist created: {len(filtered_df)} users")
    print(f"   File: {output_path}")
    return output_path


def upload_to_azure(file_path: Path, environment: str) -> None:
    """Upload allowlist file to Azure Blob Storage."""
    print(f"🔄 Uploading {environment} allowlist to Azure...")

    secrets = dotenv_values()
    blob_path = "lookups/allowlist.csv"
    container = secrets["AZURE_STORAGE_CONTAINER_NAME"]

    if environment == "dev":
        connection_string = secrets["AZURE_STORAGE_CONNECTION_STRING"]
    elif environment == "prod":
        connection_string = secrets["AZURE_STORAGE_CONNECTION_STRING_PROD"]
    else:
        raise ValueError(f"Unknown environment: {environment}")

    _upload_with_connection_string(connection_string, container, blob_path, file_path)
    print(f"✅ {environment.title()} allowlist uploaded to Azure")


def update_dev_allowlist() -> None:
    """Update the development allowlist."""
    print("🚀 Updating development allowlist...")
    file_path = create_allowlist("dev")
    upload_to_azure(file_path, "dev")
    print("✅ Development allowlist updated successfully!")


def update_prod_allowlist() -> None:
    """Update the production allowlist."""
    print("🚀 Updating production allowlist...")
    file_path = create_allowlist("prod")
    upload_to_azure(file_path, "prod")
    print("✅ Production allowlist updated successfully!")


def update_both_allowlists() -> None:
    """Update both development and production allowlists."""
    print("🚀 Updating both allowlists...")

    # Create both files
    dev_file = create_allowlist("dev")
    prod_file = create_allowlist("prod")

    # Upload both to Azure
    upload_to_azure(dev_file, "dev")
    upload_to_azure(prod_file, "prod")

    print("✅ Both allowlists updated successfully!")


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Update allowlist files and upload to Azure"
    )
    parser.add_argument(
        "--env",
        choices=["dev", "prod", "both"],
        default="both",
        help="Environment to update (dev, prod, or both)",
    )

    args = parser.parse_args()

    try:
        if args.env == "dev":
            update_dev_allowlist()
        elif args.env == "prod":
            update_prod_allowlist()
        elif args.env == "both":
            update_both_allowlists()
    except Exception as e:
        print(f"❌ Error updating allowlist: {e}")
        raise


if __name__ == "__main__":
    main()
