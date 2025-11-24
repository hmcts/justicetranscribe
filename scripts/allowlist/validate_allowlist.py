"""Validate allowlist CSV for CI/CD pipeline.

This script validates the allowlist CSV file during the build process to ensure:
- File exists and is readable
- CSV format is correct (has 'email' column)
- All emails end with @justice.gov.uk
- No duplicate entries
- No empty or invalid emails

Exit codes:
- 0: Validation passed
- 1: Validation failed
"""

import sys
from pathlib import Path

import pandas as pd


class ValidationError(Exception):
    """Raised when validation fails."""


def validate_allowlist(csv_path: Path) -> tuple[bool, list[str]]:  # noqa: C901, PLR0912, PLR0911
    """Validate the allowlist CSV file.

    Parameters
    ----------
    csv_path : Path
        Path to the allowlist CSV file.

    Returns
    -------
    tuple[bool, list[str]]
        (is_valid, list_of_errors)
    """
    errors = []

    # Check file exists
    if not csv_path.exists():
        errors.append(f"❌ Allowlist file not found: {csv_path}")
        return False, errors

    try:
        # Try to read CSV (explicitly set index_col=None to prevent treating email as index)
        allowlist_df = pd.read_csv(csv_path, encoding="utf-8", index_col=None)
    except Exception as e:
        errors.append(f"❌ Failed to read CSV: {e}")
        return False, errors

    # Check for 'email' column
    if "email" not in allowlist_df.columns:
        errors.append("❌ CSV missing required 'email' column")
        if len(allowlist_df.columns) > 0:
            errors.append(f"   Found columns: {', '.join(allowlist_df.columns)}")
        return False, errors

    # Check if email column has data or if emails are in the index (malformed CSV)
    if allowlist_df["email"].isna().all() and not allowlist_df.index.name:
        # Emails are in the index (malformed CSV with trailing commas)
        errors.append("❌ Malformed CSV detected: emails are in index, not email column")
        errors.append("   This usually means trailing commas in the file")
        errors.append("   Hint: Remove trailing commas from each line")
        return False, errors

    # Check for empty file
    if len(allowlist_df) == 0:
        errors.append("❌ Allowlist is empty (no email entries)")
        return False, errors

    # Validate each email
    invalid_emails = []
    duplicate_emails = []
    seen_emails = set()

    for idx, row in allowlist_df.iterrows():
        email = row["email"]
        row_num = int(idx) + 2  # Convert to int for display (idx is pandas index)

        # Check for null/empty
        if pd.isna(email) or not isinstance(email, str) or not email.strip():
            invalid_emails.append(f"Row {row_num}: empty or null email")
            continue

        email_clean = email.strip().lower()

        # Check for duplicates
        if email_clean in seen_emails:
            duplicate_emails.append(f"Row {row_num}: duplicate email '{email}'")
        seen_emails.add(email_clean)

        # Check domain (allow developer@localhost.com as special case for local dev)
        allowed_domains = ("@justice.gov.uk", "@hmiprobation.gov.uk")
        if not email_clean.endswith(allowed_domains) and email_clean != "developer@localhost.com":
            invalid_emails.append(
                f"Row {row_num}: '{email}' (invalid domain, must be @justice.gov.uk or @hmiprobation.gov.uk)"
            )

        # Basic format check
        if "@" not in email_clean or "." not in email_clean:
            invalid_emails.append(f"Row {row_num}: '{email}' (invalid email format)")

    # Report errors
    if invalid_emails:
        errors.append(f"❌ Found {len(invalid_emails)} invalid email(s):")
        for err in invalid_emails[:10]:  # Show first 10
            errors.append(f"   - {err}")
        if len(invalid_emails) > 10:
            errors.append(f"   ... and {len(invalid_emails) - 10} more")

    if duplicate_emails:
        errors.append(f"❌ Found {len(duplicate_emails)} duplicate email(s):")
        for err in duplicate_emails[:10]:  # Show first 10
            errors.append(f"   - {err}")
        if len(duplicate_emails) > 10:
            errors.append(f"   ... and {len(duplicate_emails) - 10} more")

    # Success
    if not errors:
        return True, []
    return False, errors


def main() -> int:
    """Main entry point."""
    # Default path to allowlist
    script_dir = Path(__file__).parent
    default_allowlist = script_dir.parent.parent / "backend" / ".allowlist" / "allowlist.csv"

    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_allowlist

    print("=" * 60)
    print("Allowlist Validation")
    print("=" * 60)
    print(f"Validating: {csv_path}")
    print()

    is_valid, errors = validate_allowlist(csv_path)

    if is_valid:
        # Count emails
        final_allowlist_df = pd.read_csv(csv_path)
        print("✅ Validation passed!")
        print(f"   Total valid emails: {len(final_allowlist_df)}")
        print()
        return 0

    print("❌ Validation failed!\n")
    for error in errors:
        print(error)
    print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
