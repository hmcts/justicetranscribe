"""Test CORS security filtering for wildcard patterns."""

import pytest
from urllib.parse import urlsplit


def parse_origins(val: str | None) -> list[str]:
    """Parse and normalize CORS origins from environment variable.
    
    Handles comma and whitespace separated values, normalizes URLs,
    and filters out wildcards for security.
    """
    if not val:
        return []
    
    # Split on comma or whitespace
    raw = [p.strip() for chunk in val.split(",") for p in chunk.split() if p.strip()]
    
    # Drop wildcards & dedupe; normalize to scheme://host[:port]
    out = []
    for o in raw:
        # Reject any origin containing wildcards anywhere
        if "*" in o:
            continue
            
        parts = urlsplit(o)
        if parts.scheme and parts.netloc:
            # Normalize to scheme://host format, removing default ports
            host = parts.netloc
            # Check if port is default and remove it
            if parts.port is not None:
                if (parts.scheme == "https" and parts.port == 443) or (parts.scheme == "http" and parts.port == 80):
                    # Remove the port from netloc - use hostname if available, otherwise reconstruct
                    if parts.hostname:
                        host = parts.hostname
                    else:
                        # Fallback: reconstruct hostname from netloc
                        host = parts.netloc.split(":")[0]
                
            normalized = f"{parts.scheme}://{host}"
            if normalized not in out:
                out.append(normalized)
    return out


class TestCORSWildcardFiltering:
    """Test that wildcard patterns are properly filtered out."""

    def test_rejects_leading_wildcard(self):
        """Test that origins starting with * are rejected."""
        origins = "*,https://example.com,http://localhost:3000"
        result = parse_origins(origins)
        assert result == ["https://example.com", "http://localhost:3000"]

    def test_rejects_internal_wildcards(self):
        """Test that origins with wildcards in domain are rejected."""
        origins = "https://*.example.com,https://sub.*.example.com,https://example.com"
        result = parse_origins(origins)
        assert result == ["https://example.com"]

    def test_rejects_trailing_wildcards(self):
        """Test that origins ending with * are rejected."""
        origins = "https://example.com/*,https://example.com,http://localhost:3000"
        result = parse_origins(origins)
        assert result == ["https://example.com", "http://localhost:3000"]

    def test_rejects_multiple_wildcards(self):
        """Test that origins with multiple wildcards are rejected."""
        origins = "https://*.*.example.com,https://example.com"
        result = parse_origins(origins)
        assert result == ["https://example.com"]

    def test_rejects_wildcard_in_path(self):
        """Test that wildcards in URL path are rejected."""
        origins = "https://example.com/*,https://example.com"
        result = parse_origins(origins)
        assert result == ["https://example.com"]

    def test_rejects_wildcard_in_scheme(self):
        """Test that wildcards in scheme are rejected."""
        origins = "https*://example.com,https://example.com"
        result = parse_origins(origins)
        assert result == ["https://example.com"]

    def test_accepts_valid_origins(self):
        """Test that valid origins without wildcards are accepted."""
        origins = "https://example.com,http://localhost:3000,https://subdomain.example.com"
        result = parse_origins(origins)
        expected = [
            "https://example.com",
            "http://localhost:3000", 
            "https://subdomain.example.com"
        ]
        assert result == expected

    def test_handles_empty_input(self):
        """Test that empty input returns empty list."""
        assert parse_origins("") == []
        assert parse_origins(None) == []

    def test_handles_whitespace_separated(self):
        """Test that whitespace-separated origins work."""
        origins = "https://example.com  http://localhost:3000  https://test.com"
        result = parse_origins(origins)
        expected = ["https://example.com", "http://localhost:3000", "https://test.com"]
        assert result == expected

    def test_deduplicates_origins(self):
        """Test that duplicate origins are removed."""
        origins = "https://example.com,https://example.com,http://localhost:3000"
        result = parse_origins(origins)
        assert result == ["https://example.com", "http://localhost:3000"]

    def test_normalizes_urls(self):
        """Test that URLs are normalized to scheme://host format."""
        origins = "https://example.com:443/path,http://localhost:3000/other,https://test.com:8080"
        result = parse_origins(origins)
        assert result == ["https://example.com", "http://localhost:3000", "https://test.com:8080"]

    def test_normalizes_default_ports(self):
        """Test that default ports (80 for HTTP, 443 for HTTPS) are removed."""
        origins = "https://example.com:443,http://example.com:80,https://test.com:8080"
        result = parse_origins(origins)
        assert result == ["https://example.com", "http://example.com", "https://test.com:8080"]

    def test_rejects_invalid_urls(self):
        """Test that invalid URLs are rejected."""
        origins = "not-a-url,https://example.com,also-invalid"
        result = parse_origins(origins)
        assert result == ["https://example.com"]
