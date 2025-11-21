"""Simple allowlist management using local CSV file."""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Default path to the allowlist CSV file
DEFAULT_ALLOWLIST_PATH = Path(__file__).parent.parent / ".allowlist" / "allowlist.csv"


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

        VALIDATION STRATEGY:
        - Build time (CI/CD): Strict validation of email format and @justice.gov.uk domain
        - Runtime: Simplified loading - just normalize and deduplicate

        FAIL-OPEN: Returns empty set if file missing/unreadable (triggers fail-open).

        Returns
        -------
        set[str]
            Set of lowercase, normalized email addresses.
            Returns empty set if file doesn't exist or has no entries.
        """
        if not self.csv_path.exists():
            logger.warning("Allowlist file not found: %s - returning empty set", self.csv_path)
            return set()

        try:
            # Read CSV file
            allowlist_df = pd.read_csv(self.csv_path)

            # Normalize column names to lowercase
            allowlist_df.columns = allowlist_df.columns.str.lower().str.strip()

            # Check for required email column
            if "email" not in allowlist_df.columns:
                logger.warning(
                    "CSV must contain 'email' column. Found: %s - returning empty set", list(allowlist_df.columns)
                )
                return set()

            # Extract and normalize emails
            # Validation (format, domain) happens at build time via CI/CD
            # Runtime just loads and normalizes
            emails = allowlist_df["email"].astype(str).str.strip().str.lower()

            # Filter out only null/empty entries
            valid_emails = emails[(emails.str.len() > 0) & (emails != "nan")]

            # Count how many were filtered out
            filtered_count = len(emails) - len(valid_emails)
            if filtered_count > 0:
                logger.warning("Filtered out %d empty/null emails from allowlist", filtered_count)

            # Remove duplicates and convert to set
            email_set = set(valid_emails.unique())

            if not email_set:
                logger.warning("No valid emails found in allowlist - returning empty set")
                return set()

            logger.info("Loaded %d valid emails from allowlist: %s", len(email_set), self.csv_path)
        except Exception:
            logger.exception("Failed to parse allowlist CSV - returning empty set")
            return set()
        else:
            return email_set

    def is_user_allowlisted(self, email: str | None) -> bool:
        """Check if an email is in the allowlist.

        FAIL-OPEN: Any exception during checking returns True (allows access).
        Empty allowlist (file missing, no valid emails) also returns True.
        This ensures system errors don't block all users from the product.

        Parameters
        ----------
        email : str | None
            The email address to check.

        Returns
        -------
        bool
            True if the email is allowlisted or if there's an error checking.
            False only if email is explicitly not in the allowlist.
        """
        if not email:
            return False

        try:
            # Load allowlist on first use (lazy loading)
            if self._allowed_emails is None:
                self._allowed_emails = self._load_allowlist()

            # FAIL-OPEN: If allowlist is empty (file missing, no valid emails), allow access
            if not self._allowed_emails:
                logger.warning(
                    "⚠️ ALLOWLIST IS EMPTY - FAILING OPEN ⚠️ | Email: %s | "
                    "Allowing access because allowlist has no valid entries",
                    email,
                )
                return True

            # Normalize and check email
            normalized_email = email.lower().strip()
            is_allowed = normalized_email in self._allowed_emails

            if not is_allowed:
                logger.info("User not in allowlist: %s", normalized_email)
        except Exception:
            # FAIL-OPEN: On any error, allow access
            logger.exception(
                "⚠️ ALLOWLIST CHECK FAILED - FAILING OPEN ⚠️ | Email: %s | "
                "Allowing access to prevent blocking users due to system error",
                email,
            )
            return True
        else:
            return is_allowed

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
