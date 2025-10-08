"""Create a timestamped allowlist update CSV from clipboard/stdin input.

Usage:
    # Interactive mode (paste from clipboard):
    python create_allowlist_update.py --env prod --provider "new-region"
    
    # Pipe mode:
    echo "user1@justice.gov.uk\nuser2@justice.gov.uk" | python create_allowlist_update.py --env dev --provider "test"
    
    # From file:
    cat emails.txt | python create_allowlist_update.py --env prod --provider "wales"
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd
from pyprojroot import here


def create_filename_friendly_timestamp() -> str:
    """Create a timestamp string suitable for filenames (no colons)."""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def parse_input(text: str, default_provider: str = None) -> list[tuple[str, str]]:
    """Parse input text and extract email addresses with providers.
    
    Supports multiple formats:
    - One email per line (uses default_provider)
    - Comma-separated emails (uses default_provider)
    - email,provider format (uses provided provider, or "unknown" if empty)
    - Mixed whitespace and delimiters
    
    Args:
        text: Input text containing emails
        default_provider: Default provider to use when not specified in input
        
    Returns:
        List of (email, provider) tuples
    """
    email_provider_pairs = []
    
    # Split by newlines
    for line in text.strip().split('\n'):
        if not line.strip():
            continue
            
        # Handle CSV format (email,provider) or just emails
        parts = [p.strip() for p in line.split(',')]
        
        # Extract email (first part)
        email = parts[0].strip()
        email = email.rstrip('>')  # Remove trailing > from malformed emails
        
        # Extract provider (second part if exists)
        if len(parts) > 1 and parts[1].strip():
            # Provider specified in input
            provider = parts[1].strip()
        elif len(parts) > 1 and not parts[1].strip():
            # Empty provider in CSV format
            provider = "unknown"
        elif default_provider:
            # No provider in input, use default
            provider = default_provider
        else:
            # No provider anywhere, use unknown
            provider = "unknown"
        
        # Basic validation - must contain @
        if email and '@' in email:
            email_provider_pairs.append((email, provider))
    
    return email_provider_pairs


def normalize_email(email: str) -> str:
    """Normalize email address to lowercase and strip whitespace."""
    return email.lower().strip()


def create_allowlist_update(environment: str, email_provider_pairs: list[tuple[str, str]]) -> Path:
    """Create a timestamped allowlist update CSV.
    
    Args:
        environment: 'dev' or 'prod'
        email_provider_pairs: List of (email, provider) tuples
        
    Returns:
        Path to the created CSV file
    """
    if environment not in ["dev", "prod"]:
        raise ValueError(f"Environment must be 'dev' or 'prod', got: {environment}")
    
    if not email_provider_pairs:
        raise ValueError("No valid email addresses provided")
    
    # Normalize and deduplicate
    seen = set()
    unique_pairs = []
    for email, provider in email_provider_pairs:
        normalized_email = normalize_email(email)
        normalized_provider = provider.lower().strip() if provider else "unknown"
        
        # Use email as dedup key (keep first occurrence's provider)
        if normalized_email not in seen:
            seen.add(normalized_email)
            unique_pairs.append((normalized_email, normalized_provider))
    
    # Create DataFrame
    df = pd.DataFrame(unique_pairs, columns=['email', 'provider'])
    
    # Create filename with timestamp
    timestamp = create_filename_friendly_timestamp()
    filename = f"{environment}-allowlist-update-{timestamp}.csv"
    output_path = here("data") / filename
    
    # Save CSV with headers for clarity
    df.to_csv(output_path, index=False, header=True, encoding="utf-8")
    
    # Count providers
    provider_counts = df['provider'].value_counts().to_dict()
    
    return output_path, provider_counts


def main():
    """Main function to handle command line arguments and stdin input."""
    parser = argparse.ArgumentParser(
        description="Create a timestamped allowlist update CSV from stdin/clipboard input",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Interactive mode - paste emails when prompted:
    python create_allowlist_update.py --env prod --provider "wales"
    
    # Pipe from clipboard (macOS):
    pbpaste | python create_allowlist_update.py --env dev --provider "test"
    
    # Pipe from file:
    cat emails.txt | python create_allowlist_update.py --env prod --provider "kss"
        """
    )
    
    parser.add_argument(
        "--env",
        choices=["dev", "prod"],
        required=True,
        help="Target environment (dev or prod)"
    )
    
    parser.add_argument(
        "--provider",
        required=False,
        default=None,
        help="Default provider/region name for emails without a provider (e.g., 'wales', 'kss', 'new-region'). If not specified and input lacks providers, defaults to 'unknown'."
    )
    
    args = parser.parse_args()
    
    try:
        # Check if data is being piped in
        if sys.stdin.isatty():
            print("📋 Paste email addresses (one per line, comma-separated, or email,provider format).")
            print("   Press Ctrl+D (Unix) or Ctrl+Z (Windows) when done:")
            if args.provider:
                print(f"   📌 Default provider: {args.provider}")
            print()
        
        # Read from stdin
        input_text = sys.stdin.read()
        
        if not input_text.strip():
            print("❌ No input provided. Please paste email addresses.", file=sys.stderr)
            sys.exit(1)
        
        # Parse emails and providers from input
        email_provider_pairs = parse_input(input_text, args.provider)
        
        if not email_provider_pairs:
            print("❌ No valid email addresses found in input.", file=sys.stderr)
            print("   Make sure emails contain '@' symbol.", file=sys.stderr)
            sys.exit(1)
        
        # Create the allowlist update file
        output_path, provider_counts = create_allowlist_update(args.env, email_provider_pairs)
        
        print()
        print(f"✅ Created {args.env} allowlist update file")
        print(f"   📁 File: {output_path}")
        print(f"   👥 Total users: {len(email_provider_pairs)}")
        print("   🏷️  Providers:")
        for provider, count in sorted(provider_counts.items()):
            print(f"      - {provider}: {count}")
        print()
        print("📝 Next steps:")
        print(f"   1. Review the file: cat {output_path}")
        print("   2. Merge it: You can manually merge this with data/pilot_users.csv")
        print(f"   3. Or run: make allowlist-{args.env} to rebuild and upload")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

