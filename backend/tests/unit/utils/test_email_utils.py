"""Tests for email utility functions."""

import pytest

from utils.email_utils import emails_match


@pytest.mark.parametrize(
    ("email1", "email2", "expected", "description"),
    [
        # Case-insensitive matching
        ("user@example.com", "USER@EXAMPLE.COM", True, "uppercase should match lowercase"),
        ("User@Example.com", "user@example.com", True, "mixed case should match lowercase"),
        ("USER@EXAMPLE.COM", "user@example.com", True, "all caps should match lowercase"),

        # Identical emails
        ("user@example.com", "user@example.com", True, "identical emails should match"),
        ("test.user@domain.co.uk", "test.user@domain.co.uk", True, "identical complex emails should match"),

        # Different emails
        ("user1@example.com", "user2@example.com", False, "different local parts should not match"),
        ("admin@example.com", "user@example.com", False, "different usernames should not match"),

        # Different domains
        ("user@example.com", "user@different.com", False, "different domains should not match"),
        ("admin@gov.uk", "admin@justice.gov.uk", False, "different subdomains should not match"),

        # None values
        (None, "user@example.com", False, "None as first email should not match"),
        ("user@example.com", None, False, "None as second email should not match"),
        (None, None, False, "both None should not match"),

        # Empty strings
        ("", "user@example.com", False, "empty string as first email should not match"),
        ("user@example.com", "", False, "empty string as second email should not match"),
        ("", "", False, "both empty strings should not match"),

        # Whitespace
        ("   ", "user@example.com", False, "whitespace-only first email should not match"),
        ("user@example.com", "   ", False, "whitespace-only second email should not match"),
        ("   ", "   ", False, "both whitespace-only should not match"),

        # Complex local parts
        ("first.last+tag@example.com", "First.Last+Tag@Example.com", True, "complex emails with different cases should match"),
        ("user_name123@domain.co.uk", "USER_NAME123@DOMAIN.CO.UK", True, "emails with underscores and numbers should match case-insensitively"),
        ("first.last@example.com", "last.first@example.com", False, "different order in local part should not match"),
    ],
)
def test_emails_match(email1, email2, expected, description):
    """Test email comparison with various scenarios"""
    result = emails_match(email1, email2)
    assert result == expected, f"Failed: {description} - emails_match({email1!r}, {email2!r}) returned {result}, expected {expected}"

