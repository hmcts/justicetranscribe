"""CORS utilities for parsing and normalizing origins."""

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
