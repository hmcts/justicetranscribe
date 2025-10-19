"""
Delete all transcriptions with NULL titles and their related records.

This script:
1. Finds all Transcription records where title IS NULL
2. Deletes associated MinuteVersion records
3. Deletes associated TranscriptionJob records
4. Deletes the Transcription records
5. Leaves User records intact

Usage:
    python scripts/delete_null_title_meetings.py [--dry-run]

Options:
    --dry-run    Show what would be deleted without actually deleting
"""

import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select

from app.database.postgres_database import engine
from app.database.postgres_models import MinuteVersion, Transcription, TranscriptionJob
from app.logger import logger


def delete_null_title_transcriptions(dry_run: bool = False) -> None:
    """
    Delete all transcriptions with NULL titles and their related records.
    """
    logger.info("=" * 80)
    logger.info("Starting NULL title transcription cleanup")
    if dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
    logger.info("=" * 80)

    with Session(engine) as session:
        # Find all transcriptions with NULL titles
        transcriptions = session.exec(
            select(Transcription).where(Transcription.title == None)  # noqa: E711
        ).all()

        if not transcriptions:
            logger.info("✓ No transcriptions with NULL titles found. Database is clean!")
            return

        logger.info(f"Found {len(transcriptions)} transcription(s) with NULL titles\n")

        total_minute_versions = 0
        total_transcription_jobs = 0

        for i, transcription in enumerate(transcriptions, 1):
            transcription_id = transcription.id
            user_id = transcription.user_id
            created = transcription.created_datetime.isoformat()

            # Count related records
            minute_versions = session.exec(
                select(MinuteVersion).where(MinuteVersion.transcription_id == transcription_id)
            ).all()

            transcription_jobs = session.exec(
                select(TranscriptionJob).where(TranscriptionJob.transcription_id == transcription_id)
            ).all()

            total_minute_versions += len(minute_versions)
            total_transcription_jobs += len(transcription_jobs)

            if dry_run:
                logger.info(
                    f"[{i}/{len(transcriptions)}] [DRY RUN] Would delete transcription {transcription_id}\n"
                    f"  User: {user_id}\n"
                    f"  Created: {created}\n"
                    f"  Related: {len(minute_versions)} minute version(s), "
                    f"{len(transcription_jobs)} transcription job(s)"
                )
            else:
                # Delete in correct order (children first due to foreign keys)

                # 1. Delete minute versions
                for mv in minute_versions:
                    session.delete(mv)

                # 2. Delete transcription jobs
                for tj in transcription_jobs:
                    session.delete(tj)

                # 3. Delete transcription
                session.delete(transcription)

                logger.info(
                    f"[{i}/{len(transcriptions)}] Deleted transcription {transcription_id}\n"
                    f"  User: {user_id}\n"
                    f"  Created: {created}\n"
                    f"  Deleted: {len(minute_versions)} minute version(s), "
                    f"{len(transcription_jobs)} transcription job(s)"
                )

        # Commit all deletions
        if not dry_run:
            session.commit()
            logger.info("\n" + "=" * 80)
            logger.info("✓ Successfully deleted:")
            logger.info(f"  - {len(transcriptions)} transcription(s)")
            logger.info(f"  - {total_minute_versions} minute version(s)")
            logger.info(f"  - {total_transcription_jobs} transcription job(s)")
            logger.info("=" * 80)
        else:
            logger.info("\n" + "=" * 80)
            logger.info("[DRY RUN] Would have deleted:")
            logger.info(f"  - {len(transcriptions)} transcription(s)")
            logger.info(f"  - {total_minute_versions} minute version(s)")
            logger.info(f"  - {total_transcription_jobs} transcription job(s)")
            logger.info("Run without --dry-run to actually delete these records")
            logger.info("=" * 80)


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Delete all transcriptions with NULL titles"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )

    args = parser.parse_args()

    try:
        delete_null_title_transcriptions(dry_run=args.dry_run)
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise


if __name__ == "__main__":
    main()

