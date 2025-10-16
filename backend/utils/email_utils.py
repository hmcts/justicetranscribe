"""Email utility functions for authentication and user management."""


def emails_match(email1: str | None, email2: str | None) -> bool:
    """
    Compare two email addresses in a case-insensitive manner.

    Email addresses are case-insensitive per RFC 5321, but different
    authentication systems (e.g., Azure Easy Auth vs JWT tokens) may
    return the same email with different casing. This function ensures
    consistent comparison regardless of case.

    Parameters
    ----------
    email1 : str | None
        First email address to compare. Can be None.
    email2 : str | None
        Second email address to compare. Can be None.

    Returns
    -------
    bool
        True if both emails are non-None and match (case-insensitive),
        False otherwise.
    """
    if not email1 or not email2:
        return False
    # Strip whitespace and check if both are non-empty
    email1_stripped = email1.strip()
    email2_stripped = email2.strip()
    if not email1_stripped or not email2_stripped:
        return False
    return email1_stripped.lower() == email2_stripped.lower()
