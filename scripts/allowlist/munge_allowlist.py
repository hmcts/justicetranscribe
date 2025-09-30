"""A script to ingest allowlist csv, prep and save to blob storage.

Data dependencies:
* data/allowlist.csv
* data/pilot_users.csv

Output:
* data/allowlist_final.csv
"""

from pathlib import Path

from azure.storage.blob import BlobServiceClient
from dotenv import dotenv_values
import pandas as pd
from pyprojroot import here




def main():


    def _upload_with_connection_string(
        connection_string: str, container: str, blob_path: str, file_path: Path
    ) -> None:
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


    secrets = dotenv_values()
    allowlist_pth = here("data/allowlist.csv")
    # need to use windows compat codec, utf-8 error
    df = pd.read_csv(allowlist_pth, encoding="cp1252")
    df = df.dropna().drop_duplicates()
    df = df.loc[df["Active/Inactive Staff"] == "Active", :].reset_index(drop=True)
    wales = df.loc[df["Provider"] == "Wales"].reset_index(drop=True)
    kssr = df.loc[df["Provider"] == "Kent Surrey Sussex Region"].reset_index(drop=True)
    allowed_wales = wales.sample(1000, random_state=41, replace=False)
    allowed_kssr = kssr.sample(1000, random_state=41, replace=False)
    allowed = pd.concat([allowed_wales, allowed_kssr], ignore_index=True)
    keep_cols = ["Provider", "Email"]
    allowed = allowed[keep_cols]

    allowed.columns = map(str.lower, allowed.columns)
    for k, v in allowed.iterrows():
        if v["provider"] == "Kent Surrey Sussex Region":
            v["provider"] = "kss"

    # Ai Justice Unit team members, commented out members used to test logic in dev
    ai_justice_unit = pd.DataFrame(
        {
            "email": [
                # "ayse.mutlu@justice.gov.uk",
                "dan.james@justice.gov.uk",
                # "developer@localhost.com",
                "franziska.hasford@justice.gov.uk",
                "john.daley@justice.gov.uk",
                # "louis.allgood@justice.gov.uk",
                "richard.leyshon@justice.gov.uk",
                ],
        }
    )
    ai_justice_unit["provider"] = "Ai Justice Unit"
    allowed = pd.concat([allowed, ai_justice_unit], ignore_index=True)

    # pilot members
    pilot_pth = here("data/pilot_users.csv")
    pilot_df = pd.read_csv(pilot_pth, encoding="cp1252", names=["email", "provider"])
    allowed = pd.concat([allowed, pilot_df], ignore_index=True)

    # manually onboarded members
    manually_onboarded = pd.DataFrame.from_records(
        [
            ("adele.alenizy@justice.gov.uk", "Wales"),
            ("clare.phillips@justice.gov.uk", "Wales"),
            ("helen.smith11@justice.gov.uk", "Wales"),
            ("jessamine.stonehouse@justice.gov.uk", "HQ-DPM"),
            ("louisa.chatterton@justice.gov.uk", "HQ-DPM"),
            ("samantha.merrett@justice.gov.uk", "HQ-DAT"),
            ("matt.proctor-leake@justice.gov.uk", "HQ-DAT"),
        ],
        columns=["email", "provider"],
    )
    allowed = pd.concat([allowed, manually_onboarded], ignore_index=True)
    # lowercase all provider values
    allowed["provider"] = allowed["provider"].apply(lambda x: x.lower().strip())
    allowed = allowed.drop_duplicates()

    #  sanity - lower everything
    for col in allowed.columns:
        allowed[col] = allowed[col].apply(lambda x: x.lower().strip())
    # rebuild lookup for dev with everything lowered
    ai_justice_unit = allowed.query(
        "provider == 'ai justice unit'"
        ).reset_index(drop=True)

    # Always write UTF-8 for backend readers
    output_path = here("data/allowlist_final.csv")
    allowed.to_csv(output_path, index=False, encoding="utf-8")
    ai_justice_pth = here("data/allowlist_dev.csv")
    ai_justice_unit.to_csv(ai_justice_pth, index=False, encoding="utf-8")

    # azure operations 
    BLOB_PTH = "lookups/allowlist.csv"
    conn_dev = secrets["AZURE_STORAGE_CONNECTION_STRING"]
    conn_prod = secrets["AZURE_STORAGE_CONNECTION_STRING_PROD"]
    container = secrets["AZURE_STORAGE_CONTAINER_NAME"]
    _upload_with_connection_string(conn_prod, container, BLOB_PTH, output_path)
    #  dev allowlist should contain team only
    _upload_with_connection_string(conn_dev, container, BLOB_PTH, ai_justice_pth)


if __name__ == "__main__":
    main()
