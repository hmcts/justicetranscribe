"""
Blob Deletion Service for automated cleanup of audio files after transcription completion.

This service handles the automated deletion of MP4 audio files from Azure Blob Storage
once transcription has been successfully completed and stored in PostgreSQL.
"""

import asyncio
from uuid import UUID

import sentry_sdk
from sqlalchemy import select

from app.audio.azure_utils import AsyncAzureBlobManager
from app.database.connection import get_async_session
from app.database.postgres_models import TranscriptionJob
from app.logger import logger
from utils.settings import get_settings


class BlobDeletionService:
    """
    Service for automated blob deletion after transcription completion.

    This service provides methods to:
    - Verify transcription completion in the database
    - Delete audio blobs from Azure Storage with retry logic
    - Handle cleanup failures and flag records for manual intervention
    """

    def __init__(self):
        """Initialize the blob deletion service."""
        self.settings = get_settings()
        self.azure_blob_manager = AsyncAzureBlobManager()
        self.max_retry_attempts = 3
        self.retry_delay_seconds = 5

    async def verify_transcription_completion(self, transcription_job_id: UUID) -> bool:
        """
        Verify that a transcription job has been completed successfully.

        Args:
            transcription_job_id: The UUID of the transcription job to verify

        Returns:
            bool: True if transcription is complete and successful, False otherwise
        """
        try:
            async with get_async_session() as session:
                # Query the transcription job
                stmt = select(TranscriptionJob).where(
                    TranscriptionJob.id == transcription_job_id
                )
                result = await session.execute(stmt)
                transcription_job = result.scalar_one_or_none()

                if not transcription_job:
                    logger.warning(
                        f"Transcription job {transcription_job_id} not found"
                    )
                    return False

                # Check if transcription has dialogue entries (indicates successful completion)
                if not transcription_job.dialogue_entries:
                    logger.warning(
                        f"Transcription job {transcription_job_id} has no dialogue entries"
                    )
                    return False

                # Check if there's an error message (indicates failure)
                if transcription_job.error_message:
                    logger.warning(
                        f"Transcription job {transcription_job_id} has error: {transcription_job.error_message}"
                    )
                    return False

                logger.info(
                    f"Transcription job {transcription_job_id} verified as completed successfully"
                )
                return True

        except Exception as e:
            logger.error(
                f"Failed to verify transcription completion for {transcription_job_id}: {e}"
            )
            return False

    async def delete_audio_blob(
        self, blob_path: str, transcription_job_id: UUID
    ) -> bool:
        """
        Delete an audio blob from Azure Storage with retry logic.

        Args:
            blob_path: The path to the blob in Azure Storage
            transcription_job_id: The UUID of the transcription job
            user_email: The email of the user who uploaded the file

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        logger.info(
            f"Starting blob deletion for {blob_path} (job: {transcription_job_id})"
        )

        for attempt in range(1, self.max_retry_attempts + 1):
            try:
                # Check if blob exists before attempting deletion
                if not await self.azure_blob_manager.blob_exists(blob_path):
                    logger.warning(
                        f"Blob {blob_path} does not exist, skipping deletion"
                    )
                    return True  # Consider this a success since the goal is achieved

                # Attempt deletion
                success = await self.azure_blob_manager.delete_blob(blob_path)

                if success:
                    logger.info(
                        f"Successfully deleted blob {blob_path} on attempt {attempt}"
                    )
                    return True
                else:
                    logger.warning(
                        f"Failed to delete blob {blob_path} on attempt {attempt}"
                    )

            except Exception as e:
                logger.error(
                    f"Exception during blob deletion attempt {attempt} for {blob_path}: {e}"
                )

            # Wait before retry (except on last attempt)
            if attempt < self.max_retry_attempts:
                logger.info(
                    f"Retrying blob deletion in {self.retry_delay_seconds} seconds..."
                )
                await asyncio.sleep(self.retry_delay_seconds)

        # All retry attempts failed
        error_msg = f"Failed to delete blob {blob_path} after {self.max_retry_attempts} attempts"
        logger.error(error_msg)
        sentry_sdk.capture_exception(error_msg)
        return False

    async def process_transcription_cleanup(
        self, transcription_job_id: UUID, blob_path: str
    ) -> bool:
        """
        Complete workflow for processing transcription cleanup.

        This method:
        1. Verifies the transcription was completed successfully
        2. Deletes the audio blob from Azure Storage
        3. Updates the database with cleanup status

        Args:
            transcription_job_id: The UUID of the transcription job
            blob_path: The path to the blob in Azure Storage
            user_email: The email of the user who uploaded the file

        Returns:
            bool: True if the entire cleanup process was successful, False otherwise
        """
        logger.info(
            f"Starting transcription cleanup process for job {transcription_job_id}"
        )

        # Step 1: Verify transcription completion
        if not await self.verify_transcription_completion(transcription_job_id):
            logger.error(
                f"Transcription job {transcription_job_id} not completed successfully, skipping cleanup"
            )
            return False

        # Step 2: Delete the audio blob
        deletion_success = await self.delete_audio_blob(blob_path, transcription_job_id)

        if deletion_success:
            logger.info(
                f"Transcription cleanup completed successfully for job {transcription_job_id}"
            )
        else:
            logger.error(f"Transcription cleanup failed for job {transcription_job_id}")

        return deletion_success

    async def get_jobs_needing_cleanup(self) -> list[TranscriptionJob]:
        """
        Get all transcription jobs that need manual cleanup.

        Returns:
            list[TranscriptionJob]: List of transcription jobs flagged for manual cleanup
        """
        try:
            async with get_async_session() as session:
                stmt = select(TranscriptionJob).where(TranscriptionJob.needs_cleanup)
                result = await session.execute(stmt)
                jobs = result.scalars().all()

                logger.info(
                    f"Found {len(jobs)} transcription jobs needing manual cleanup"
                )
                return list(jobs)

        except Exception as e:
            logger.error(f"Failed to get jobs needing cleanup: {e}")
            return []
