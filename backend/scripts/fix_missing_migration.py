#!/usr/bin/env python3
"""
Script to fix the missing migration issue after reverting a PR.

This script updates the alembic_version table to the correct revision
when a migration file has been deleted but the database still references it.

This script is designed to run automatically on startup and is idempotent.

Usage:
    # Automatic mode (safe for startup, no prompts)
    python scripts/fix_missing_migration.py
    # Manual mode with confirmation
    python scripts/fix_missing_migration.py --target-revision a8f2c9d5e1b3 --interactive
"""
import argparse
import os
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

from utils.settings import get_settings

settings = get_settings()


# Map of missing revisions to their replacement revisions
# Add entries here when you revert a PR with a migration
MISSING_REVISION_MAP = {
    "758d4879be2e": "34a9930bd1f7",  # Reverted PR - rollback to before it
}


def get_available_revisions():
    """Get list of all available migration revisions from the versions directory."""
    versions_dir = Path(__file__).parent.parent / "alembic" / "versions"
    revisions = set()

    if not versions_dir.exists():
        return revisions

    for file in versions_dir.glob("*.py"):
        if file.name.startswith("__"):
            continue
        # Extract revision ID from filename (format: {revision}_{description}.py)
        revision = file.name.split("_")[0]
        revisions.add(revision)

    return revisions


def get_current_revision(engine):
    """Get the current revision from the database."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            row = result.fetchone()
            return row[0] if row else None
    except Exception as e:
        print(f"Warning: Could not read alembic_version table: {e}")
        return None


def update_revision(engine, current: str, target: str, interactive: bool = False):
    """Update the alembic_version table to the target revision."""
    print(f"📋 Current revision in database: {current}")
    print(f"📋 Target revision: {target}")

    if current == target:
        print("✅ Database is already at the target revision. No action needed.")
        return True

    if interactive:
        # Confirm before proceeding in interactive mode
        response = input(f"\n⚠️  This will update the migration state from '{current}' to '{target}'.\n"
                        "Make sure you understand the implications. Continue? (yes/no): ")

        if response.lower() != "yes":
            print("Aborted.")
            return False

    try:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE alembic_version SET version_num = :revision"),
                {"revision": target}
            )

        print(f"✅ Successfully updated revision from {current} to {target}")

        # Verify
        new_revision = get_current_revision(engine)
        if new_revision == target:
            print(f"✅ Verified current revision: {new_revision}")
            return True
        else:
            print(f"❌ Verification failed. Expected {target}, got {new_revision}")
            return False

    except Exception as e:
        print(f"❌ Error updating revision: {e}")
        if not interactive:
            # In automatic mode, don't exit - let migrations handle it
            return False
        sys.exit(1)


def reverse_migration_changes(engine, dry_run: bool = False):
    """
    Reverse any schema changes made by the missing migration.
    ⚠️  YOU NEED TO CUSTOMIZE THIS FUNCTION based on what the reverted
    migration actually did. Common operations:
    - Drop tables
    - Drop columns
    - Drop indexes
    - Revert data changes
    """
    print("\n" + "="*60)
    print("SCHEMA REVERSAL SECTION")
    print("="*60)

    # Example operations (commented out):

    # operations = [
    #     "DROP INDEX IF EXISTS ix_some_index",
    #     "ALTER TABLE some_table DROP COLUMN IF EXISTS some_column",
    #     "DROP TABLE IF EXISTS some_table CASCADE",
    # ]

    operations = []

    if not operations:
        print("ℹ️  No schema reversal operations defined.")  # noqa: RUF001
        print("   If the missing migration made schema changes, you should:")
        print("   1. Identify what it changed (tables, columns, indexes, etc.)")
        print("   2. Add SQL statements above to reverse those changes")
        return

    print(f"Found {len(operations)} reversal operations:")
    for i, op in enumerate(operations, 1):
        print(f"  {i}. {op}")

    if dry_run:
        print("\n[DRY RUN] Would execute the above operations")
        return

    response = input("\n⚠️  Execute these schema changes? (yes/no): ")
    if response.lower() != "yes":
        print("Skipped schema reversal.")
        return

    try:
        with engine.begin() as conn:
            for op in operations:
                print(f"Executing: {op}")
                conn.execute(text(op))

        print("✅ Schema reversal completed")

    except Exception as e:
        print(f"❌ Error during schema reversal: {e}")
        sys.exit(1)


def check_and_fix_missing_migrations(interactive: bool = False):
    """
    Automatically check for missing migrations and fix them.
    This function is designed to run on startup and is idempotent.
    It checks if the current database revision is missing from the codebase
    and automatically fixes it using the MISSING_REVISION_MAP.
    Returns:
        bool: True if no issues or successfully fixed, False if there's a problem
    """
    try:
        # Add connection timeout and retry logic
        engine = create_engine(
            settings.DATABASE_CONNECTION_STRING,
            pool_pre_ping=True,  # Verify connections before using
            connect_args={"connect_timeout": 10}
        )
        current = get_current_revision(engine)

        if not current:
            print("ℹ️  No revision found in database. This might be a fresh database.")  # noqa: RUF001
            return True

        # Get available revisions
        available = get_available_revisions()

        # Check if current revision exists in codebase
        if current in available:
            print(f"✅ Current revision {current} is valid")
            return True

        # Current revision is missing - check if we have a fix for it
        if current not in MISSING_REVISION_MAP:
            print(f"⚠️  Current revision '{current}' is missing from codebase")
            print("ℹ️  No automatic fix configured for this revision")  # noqa: RUF001
            print("ℹ️  Add an entry to MISSING_REVISION_MAP in fix_missing_migration.py")  # noqa: RUF001
            return False

        # We have a fix - apply it
        target = MISSING_REVISION_MAP[current]
        print(f"🔧 Detected missing revision '{current}'")
        print(f"🔧 Automatically fixing by rolling back to '{target}'")

        return update_revision(engine, current, target, interactive=interactive)

    except Exception as e:
        print(f"❌ Error in check_and_fix_missing_migrations: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Fix missing migration issue by updating alembic_version table"
    )
    parser.add_argument(
        "--target-revision",
        help="The revision ID to update to (e.g., a8f2c9d5e1b3). If not provided, uses automatic detection."
    )
    parser.add_argument(
        "--reverse-changes",
        action="store_true",
        help="Also reverse schema changes made by the missing migration"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Ask for confirmation before making changes (default: automatic mode)"
    )

    args = parser.parse_args()

    print("="*60)
    print("MISSING MIGRATION RECOVERY SCRIPT")
    print("="*60)

    # Automatic mode - check and fix
    if not args.target_revision:
        print("🤖 Running in AUTOMATIC mode")
        print(f"📍 Database URL: {settings.DATABASE_CONNECTION_STRING[:50]}...")
        print("="*60 + "\n")

        success = check_and_fix_missing_migrations(interactive=args.interactive)

        if not success:
            print("\n⚠️  Could not automatically fix the issue")
            print("Run with --target-revision to manually specify the target")
            sys.exit(1)

        print("\n" + "="*60)
        print("✅ MIGRATION STATE CHECK COMPLETE")
        print("="*60)
        return

    # Manual mode with specific target
    print("🔧 Running in MANUAL mode")
    print(f"📍 Database URL: {settings.DATABASE_CONNECTION_STRING[:50]}...")
    print(f"🎯 Target revision: {args.target_revision}")
    print(f"🔄 Reverse changes: {args.reverse_changes}")
    print(f"💬 Interactive: {args.interactive}")
    print("="*60 + "\n")

    # Create engine
    engine = create_engine(settings.DATABASE_CONNECTION_STRING)

    # Step 1: Optionally reverse schema changes
    if args.reverse_changes:
        reverse_migration_changes(engine, dry_run=False)

    # Step 2: Update alembic_version table
    current = get_current_revision(engine)
    if current:
        update_revision(engine, current, args.target_revision, interactive=args.interactive)

    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Verify the migration state:")
    print("   alembic current")
    print("   alembic history")
    print("2. Run any pending migrations:")
    print("   alembic upgrade head")
    print("3. Restart your application")
    print("="*60)


if __name__ == "__main__":
    main()

