"""Add users from a CSV file to the local allowlist.

This script:
1. Loads input CSV file (flexible: handles files with/without headers)
2. Cleans and validates emails (STRICT: must end with @justice.gov.uk)
3. Merges with existing allowlist (no duplicates)
4. Saves updated allowlist
5. Outputs semicolon-separated list of newly added users

Usage:
    python add_users_to_allowlist.py --file path/to/users.csv
"""

import argparse
import sys
from pathlib import Path

import pandas as pd


def clean_email(email: str) -> str:
    """Clean and normalize email address.

    Parameters
    ----------
    email : str
        Raw email address

    Returns
    -------
    str
        Cleaned, lowercase email

    Raises
    ------
    ValueError
        If email is invalid
    """
    if pd.isna(email) or not isinstance(email, str):
        raise ValueError(f"Invalid email (null or non-string): {email}")

    # Remove leading/trailing whitespace and line breaks
    email = email.strip().lstrip("\n\r")

    # Remove trailing > character (from some email formats)
    email = email.rstrip(">")

    # Convert to lowercase
    email = email.lower()

    if not email:
        raise ValueError("Email cannot be empty after cleaning")

    return email


def validate_email(email: str) -> bool:
    """Validate email format.

    STRICT validation: Must end with @justice.gov.uk
    Exception: developer@localhost.com is allowed for local development

    Parameters
    ----------
    email : str
        Email to validate

    Returns
    -------
    bool
        True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False

    # Must contain @ symbol
    if "@" not in email:
        return False

    # Allow developer@localhost.com as special case for local dev
    if email == "developer@localhost.com":
        return True

    # Must end with @justice.gov.uk
    if not email.endswith("@justice.gov.uk"):
        return False

    return True


def load_input_csv(file_path: Path) -> pd.DataFrame:
    """Load and validate input CSV file.

    Handles files with or without headers. If no standard 'email' column is found,
    treats the first column as emails.

    Parameters
    ----------
    file_path : Path
        Path to input CSV file

    Returns
    -------
    pd.DataFrame
        DataFrame with 'email' column

    Raises
    ------
    FileNotFoundError
        If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    print(f"📂 Loading input file: {file_path}")

    # Try loading with headers first
    df = pd.read_csv(file_path, encoding="utf-8")

    # Normalize column names
    df.columns = df.columns.str.lower().str.strip()

    # Check if it has an 'email' column
    if "email" not in df.columns:
        # No email column - treat first column as emails
        print("   📝 No 'email' column found, using first column as emails")
        first_col = df.columns[0]
        df = df.rename(columns={first_col: "email"})

    # Keep only email column
    df = df[["email"]]

    print(f"📊 Loaded {len(df)} rows from input file")
    return df


def clean_and_validate_emails(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Clean and validate emails from input DataFrame.

    STRICT validation: Rejects emails that don't end with @justice.gov.uk

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with 'email' column

    Returns
    -------
    tuple[pd.DataFrame, list[str], list[str]]
        - Cleaned DataFrame with valid emails
        - List of rejected emails with reasons
        - List of valid cleaned emails
    """
    cleaned_emails = []
    rejected = []

    print("🔍 Cleaning and validating emails...")

    for idx, row in df.iterrows():
        email_raw = row["email"]

        try:
            # Clean the email
            email_clean = clean_email(email_raw)

            # Validate the email (STRICT)
            if not validate_email(email_clean):
                if "@" not in email_clean:
                    rejected.append(f"{email_raw} (missing @ symbol)")
                elif not email_clean.endswith("@justice.gov.uk"):
                    rejected.append(f"{email_raw} (must end with @justice.gov.uk)")
                else:
                    rejected.append(f"{email_raw} (invalid format)")
                continue

            cleaned_emails.append(email_clean)

        except ValueError as e:
            rejected.append(f"{email_raw} ({e!s})")

    # Create DataFrame from valid emails
    valid_df = pd.DataFrame({"email": cleaned_emails})

    # Remove duplicates within input file
    initial_count = len(valid_df)
    valid_df = valid_df.drop_duplicates(subset=["email"])
    duplicate_count = initial_count - len(valid_df)

    if duplicate_count > 0:
        print(f"   ℹ️  Removed {duplicate_count} duplicate(s) from input file")

    print(f"✅ Validated: {len(valid_df)} valid, {len(rejected)} rejected")

    return valid_df, rejected, list(valid_df["email"])


def load_existing_allowlist(allowlist_path: Path) -> pd.DataFrame:
    """Load existing allowlist CSV.

    Parameters
    ----------
    allowlist_path : Path
        Path to allowlist.csv

    Returns
    -------
    pd.DataFrame
        Existing allowlist or empty DataFrame if doesn't exist
    """
    if not allowlist_path.exists():
        print(f"⚠️  Allowlist not found at {allowlist_path}, creating new one")
        return pd.DataFrame({"email": []})

    print(f"📂 Loading existing allowlist: {allowlist_path}")
    df = pd.read_csv(allowlist_path, encoding="utf-8")

    # Normalize column names
    df.columns = df.columns.str.lower().str.strip()

    if "email" not in df.columns:
        print("⚠️  No 'email' column in existing allowlist, treating as empty")
        return pd.DataFrame({"email": []})

    print(f"📊 Existing allowlist has {len(df)} users")
    return df[["email"]]


def merge_allowlists(existing_df: pd.DataFrame, new_df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Merge existing and new allowlists.

    Parameters
    ----------
    existing_df : pd.DataFrame
        Existing allowlist
    new_df : pd.DataFrame
        New emails to add

    Returns
    -------
    tuple[pd.DataFrame, list[str]]
        - Merged DataFrame
        - List of newly added emails
    """
    print("🔄 Merging allowlists...")

    # Get existing emails as set for fast lookup
    existing_emails = set(existing_df["email"].str.lower().str.strip())

    # Find new emails
    new_emails = []
    for email in new_df["email"]:
        email_normalized = email.lower().strip()
        if email_normalized not in existing_emails:
            new_emails.append(email_normalized)

    if not new_emails:
        print("ℹ️  No new users to add - all emails already in allowlist")
        return existing_df, []

    # Combine existing and new
    all_emails = list(existing_emails) + new_emails

    # Create merged DataFrame
    merged_df = pd.DataFrame({"email": sorted(all_emails)})

    print(f"✅ Merged: {len(new_emails)} new user(s) added")
    return merged_df, new_emails


def save_allowlist(df: pd.DataFrame, allowlist_path: Path) -> None:
    """Save allowlist to CSV.

    Parameters
    ----------
    df : pd.DataFrame
        Allowlist DataFrame
    allowlist_path : Path
        Path to save allowlist
    """
    # Ensure directory exists
    allowlist_path.parent.mkdir(parents=True, exist_ok=True)

    # Save with header
    df.to_csv(allowlist_path, index=False, encoding="utf-8")
    print(f"💾 Saved allowlist: {allowlist_path} ({len(df)} total users)")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Add users from CSV to local allowlist")
    parser.add_argument("--file", type=str, required=True, help="Path to CSV file with emails to add")
    parser.add_argument(
        "--allowlist",
        type=str,
        required=False,
        help="Path to allowlist.csv file (optional, defaults to backend/.allowlist/allowlist.csv)",
    )

    args = parser.parse_args()

    # Paths
    input_path = Path(args.file)

    if args.allowlist:
        allowlist_path = Path(args.allowlist)
    else:
        script_dir = Path(__file__).parent
        allowlist_path = script_dir.parent.parent / "backend" / ".allowlist" / "allowlist.csv"

    print("\n" + "=" * 60)
    print("Add Users to Allowlist")
    print("=" * 60 + "\n")

    try:
        # Load input file
        input_df = load_input_csv(input_path)

        # Clean and validate
        valid_df, rejected, valid_emails = clean_and_validate_emails(input_df)

        # Show rejected emails if any
        if rejected:
            print("\n⚠️  Rejected emails:")
            for reason in rejected[:10]:  # Show first 10
                print(f"   - {reason}")
            if len(rejected) > 10:
                print(f"   ... and {len(rejected) - 10} more")

        if valid_df.empty:
            print("\n❌ No valid emails to add. Exiting.")
            sys.exit(1)

        # Load existing allowlist
        existing_df = load_existing_allowlist(allowlist_path)

        # Merge
        merged_df, new_users = merge_allowlists(existing_df, valid_df)

        # Save
        save_allowlist(merged_df, allowlist_path)

        # Output newly added users
        if new_users:
            print("\n" + "=" * 60)
            print(f"✅ Added {len(new_users)} new user(s) to allowlist:")
            print(";".join(new_users))
            print("=" * 60 + "\n")
        else:
            print("\n" + "=" * 60)
            print("ℹ️  No new users added - all emails were already in allowlist")
            print("=" * 60 + "\n")

        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
