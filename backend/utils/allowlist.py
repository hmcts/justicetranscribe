"""Simple allowlist management using local CSV file."""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Default path to the allowlist CSV file
DEFAULT_ALLOWLIST_PATH = Path(__file__).parent.parent.parent / ".allowlist" / "allowlist.csv"


class AllowlistManager:
    """Simple allowlist manager that reads from a local CSV file.

    The allowlist is loaded once and cached in memory. Email checks are
    case-insensitive and use a set for O(1) lookups.
    """

    def __init__(self, csv_path: str | Path | None = None) -> None:
        """Initialize the allowlist manager.

        Parameters
        ----------
        csv_path : str | Path | None
            Path to the allowlist CSV file. If None, uses default location.
        """
        self.csv_path = Path(csv_path) if csv_path else DEFAULT_ALLOWLIST_PATH
        self._allowed_emails: set[str] | None = None

    def _load_allowlist(self) -> set[str]:
        """Load and parse the allowlist CSV file.

        Returns
        -------
        set[str]
            Set of lowercase email addresses.

        Raises
        ------
        FileNotFoundError
            If the allowlist file doesn't exist.
        ValueError
            If the CSV doesn't have an 'email' column or has no valid emails.
        """
        if not self.csv_path.exists():
            error_msg = f"Allowlist file not found: {self.csv_path}"
            raise FileNotFoundError(error_msg)

        # Read CSV file
        allowlist_df = pd.read_csv(self.csv_path)

        # Normalize column names to lowercase
        allowlist_df.columns = allowlist_df.columns.str.lower().str.strip()

        # Check for required email column
        if "email" not in allowlist_df.columns:
            error_msg = f"CSV must contain 'email' column. Found: {list(allowlist_df.columns)}"
            raise ValueError(error_msg)

        # Extract and normalize emails
        emails = (
            allowlist_df["email"]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        # Filter out empty/invalid emails
        emails = emails[
            (emails.str.len() > 0) &
            (emails != "nan") &
            emails.str.contains("@", na=False)
        ]

        # Remove duplicates and convert to set
        email_set = set(emails.unique())

        if not email_set:
            error_msg = "No valid emails found in allowlist"
            raise ValueError(error_msg)

        logger.info("Loaded %d emails from allowlist: %s", len(email_set), self.csv_path)
        return email_set

    def is_user_allowlisted(self, email: str | None) -> bool:
        """Check if an email is in the allowlist.

        Parameters
        ----------
        email : str | None
            The email address to check.

        Returns
        -------
        bool
            True if the email is allowlisted, False otherwise.
        """
        if not email:
            return False

        # Load allowlist on first use
        if self._allowed_emails is None:
            try:
                self._allowed_emails = self._load_allowlist()
            except Exception:
                logger.exception("Failed to load allowlist")
                return False

        # Normalize and check email
        normalized_email = email.lower().strip()
        return normalized_email in self._allowed_emails

    def reload(self) -> None:
        """Reload the allowlist from the CSV file."""
        self._allowed_emails = None
        logger.info("Allowlist cache cleared, will reload on next check")


# Global singleton instance
_global_allowlist: AllowlistManager | None = None


def get_allowlist_manager(csv_path: str | Path | None = None) -> AllowlistManager:
    """Get the global allowlist manager instance (singleton).

    Parameters
    ----------
    csv_path : str | Path | None
        Path to the allowlist CSV file. Only used on first creation.

    Returns
    -------
    AllowlistManager
        The global allowlist manager instance.
    """
    global _global_allowlist  # noqa: PLW0603
    if _global_allowlist is None:
        _global_allowlist = AllowlistManager(csv_path)
    return _global_allowlist
