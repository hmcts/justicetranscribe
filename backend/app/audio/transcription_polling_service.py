"""
Transcription Polling Service for automatic audio file discovery and processing.

This service polls Azure Blob Storage for new audio files and automatically triggers
transcription processing without requiring frontend API calls. This avoids JWT timeout
issues on long audio recordings.
"""

import asyncio
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session, select

from app.audio.azure_utils import AsyncAzureBlobManager
from app.audio.process_audio_fully import transcribe_and_generate_llm_output
from app.audio.utils import extract_transcription_id_from_blob_path
from app.database.postgres_database import engine
from app.database.postgres_models import User
from app.logger import logger
from utils.settings import get_settings


class TranscriptionPollingService:
    """
    Service for polling Azure Blob Storage and automatically processing audio files for a specific user.

    This service:
    - Polls the user-specific prefix (user-uploads/{email}/) every 30 seconds
    - Identifies unprocessed audio files for that user only
    - Triggers transcription processing
    - Marks files as processed using blob metadata
    - Includes defensive checks to prevent cross-user data access
    """

    def __init__(self, user_email: str):
        """Initialize the transcription polling service for a specific user.

        Parameters
        ----------
        user_email : str
            Email address of the user whose files should be processed.
            Used to construct the blob prefix: user-uploads/{user_email}/
        """
        self.settings = get_settings()
        self.azure_blob_manager = AsyncAzureBlobManager()
        self.polling_interval_seconds = 30
        self.user_email = user_email
        self.user_uploads_prefix = f"user-uploads/{user_email}/"
        self.supported_extensions = {".mp4", ".webm", ".wav", ".m4a"}
        self.max_retry_attempts = 2  # Allow 2 total attempts (1 retry max as requested)
        # Record startup time - only process files uploaded after this
        self.startup_time = datetime.now(UTC)
        self._is_first_poll = True
        logger.info(
            f"Polling service initialized for user {user_email} - "
            f"will only process files uploaded after {self.startup_time.isoformat()}"
        )

    def _should_skip_blob(self, blob: dict) -> bool:
        """
        Check if a blob should be skipped when looking for files to process.

        Used during polling to filter out blobs that should NOT be transcribed:
        - Already successfully processed blobs
        - Permanently failed blobs (exceeded retry limit)
        - Blobs uploaded before service started (handled by startup cleanup)
        - Non-audio files or files belonging to other users

        Returns True if the blob should be skipped for transcription processing.

        Parameters
        ----------
        blob : dict
            Blob information dictionary.

        Returns
        -------
        bool
            True if blob should be skipped (don't process), False if it should be processed.
        """
        blob_name = blob["name"]

        # DEFENSIVE CHECK: Ensure blob belongs to this user
        if not blob_name.startswith(self.user_uploads_prefix):
            logger.warning(
                f"Security check failed: Blob '{blob_name}' does not match "
                f"user prefix '{self.user_uploads_prefix}' for user {self.user_email}"
            )
            return True

        # Check file extension
        blob_path = Path(blob_name)
        if blob_path.suffix.lower() not in self.supported_extensions:
            return True

        # Skip files uploaded before service started
        # last_modified = blob.get("last_modified")
        # if last_modified and last_modified < self.startup_time:
        #     return True

        # Check metadata for processing status
        metadata = blob.get("metadata", {})

        # Skip if already successfully processed
        if metadata.get("processed") == "true":
            return True

        # Skip if permanently failed
        if metadata.get("status") == "permanently_failed":
            logger.debug(f"User {self.user_email}: Skipping permanently failed blob: {blob_name}")
            return True

        return False

    async def poll_for_new_audio_files(self) -> list[dict]:
        """
        Poll blob storage for new, unprocessed audio files for this user only.

        Only returns files uploaded after the service started to avoid
        reprocessing old backlogged files. Includes defensive check to ensure
        all blobs belong to the user's prefix.

        Returns
        -------
        list[dict]
            List of unprocessed blob dictionaries with keys:
            - name: str (blob path)
            - metadata: dict
            - last_modified: datetime
            - size: int
        """
        try:
            # List all blobs with user-specific prefix
            all_blobs = await self.azure_blob_manager.list_blobs_in_prefix(
                prefix=self.user_uploads_prefix, include_metadata=True
            )

            # Filter for unprocessed audio files
            unprocessed = []
            for blob in all_blobs:
                if self._should_skip_blob(blob):
                    continue

                # Check retry count to avoid infinite loops
                metadata = blob.get("metadata", {})
                retry_count = int(metadata.get("retry_count", "0"))
                if retry_count >= self.max_retry_attempts:
                    logger.warning(
                        f"User {self.user_email}: Blob {blob['name']} has exceeded max retries "
                        f"({retry_count}/{self.max_retry_attempts}), marking as permanently failed"
                    )
                    await self._mark_blob_permanently_failed(blob["name"], metadata)
                    continue

                unprocessed.append(blob)

            if unprocessed:
                logger.info(f"User {self.user_email}: Found {len(unprocessed)} unprocessed audio files")

        except Exception as e:
            logger.error(f"User {self.user_email}: Error polling for new audio files: {e}")
            return []
        else:
            return unprocessed

    def extract_user_email_from_blob_path(self, blob_path: str) -> str | None:
        """
        Extract user email from blob path and verify it matches this service's user.

        Expected format: user-uploads/{email}/{filename}

        Parameters
        ----------
        blob_path : str
            The full blob path.

        Returns
        -------
        str | None
            The user email if it matches this service's user, None otherwise.
        """
        min_parts = 3  # Minimum parts for valid path: user-uploads/{email}/{filename}
        try:
            parts = blob_path.split("/")
            if len(parts) >= min_parts and parts[0] == "user-uploads":
                extracted_email = parts[1]

                # DEFENSIVE CHECK: Verify extracted email matches this service's user
                if extracted_email != self.user_email:
                    logger.error(
                        f"Security check failed: Extracted email '{extracted_email}' from blob path "
                        f"does not match service user '{self.user_email}'"
                    )
                    return None

                return extracted_email

        except Exception as e:
            logger.error(f"User {self.user_email}: Error extracting email from blob path '{blob_path}': {e}")

        return None

    def get_or_create_user_by_email(self, email: str) -> User | None:
        """
        Look up user by email in the database.

        Note: This only looks up existing users. New users must be created
        through the authentication flow.

        Parameters
        ----------
        email : str
            The user's email address.

        Returns
        -------
        User | None
            The User object if found, None otherwise.
        """
        try:
            with Session(engine) as session:
                statement = select(User).where(User.email == email)
                user = session.exec(statement).first()

                if user:
                    logger.info(f"Found user for email: {email}")
                else:
                    logger.warning(f"No user found for email: {email}")

                return user

        except Exception as e:
            logger.error(f"Error looking up user by email '{email}': {e}")
            return None

    async def process_discovered_audio(self, blob_info: dict) -> bool:
        """
        Process a discovered audio file for this user only.

        This method:
        1. Verifies blob path belongs to this user (defensive check)
        2. Extracts user email from blob path and validates it
        3. Looks up user in database
        4. Triggers transcription processing
        5. Marks blob as processed

        Parameters
        ----------
        blob_info : dict
            Dictionary containing blob information from poll_for_new_audio_files.

        Returns
        -------
        bool
            True if processing was successful, False otherwise.
        """
        blob_path = blob_info["name"]
        logger.info(f"User {self.user_email}: Processing discovered audio file: {blob_path}")

        try:
            # DEFENSIVE CHECK: Verify blob path starts with user's prefix
            if not blob_path.startswith(self.user_uploads_prefix):
                error_msg = (
                    f"Security violation: Blob path '{blob_path}' does not start with "
                    f"user prefix '{self.user_uploads_prefix}' for user {self.user_email}"
                )
                logger.error(error_msg)
                return False

            # Extract user email from path (includes additional validation)
            user_email = self.extract_user_email_from_blob_path(blob_path)
            if not user_email:
                error_msg = f"Could not extract/validate user email from blob path: {blob_path}"
                logger.error(f"User {self.user_email}: {error_msg}")
                await self._mark_blob_with_error(blob_path, error_msg)
                return False

            # Look up user in database
            user = self.get_or_create_user_by_email(user_email)
            if not user:
                error_msg = f"User not found for email: {user_email}"
                logger.error(f"User {self.user_email}: {error_msg}")
                await self._mark_blob_with_error(blob_path, error_msg)
                return False

            # Trigger transcription processing
            transcription_id = extract_transcription_id_from_blob_path(blob_path, self.user_email)

            logger.info(f"User {self.user_email}: Starting transcription for blob: {blob_path}")

            await transcribe_and_generate_llm_output(
                user_upload_blob_storage_file_key=blob_path,
                user_id=user.id,
                user_email=user.email,
                transcription_id=transcription_id,
            )

            # Mark blob as processed
            await self._mark_blob_as_processed_and_soft_delete(blob_path)

            logger.info(f"User {self.user_email}: Successfully processed audio file: {blob_path}")

        except Exception as e:
            error_msg = f"Error processing audio file {blob_path}: {e}"
            logger.error(f"User {self.user_email}: {error_msg}")
            await self._mark_blob_with_error(blob_path, str(e))
            return False
        else:
            return True

    async def _mark_blob_as_processed_and_soft_delete(self, blob_path: str) -> None:
        """
        Mark a blob as processed by setting metadata, then delete it.

        Parameters
        ----------
        blob_path : str
            The blob path.
        """
        try:
            # First mark as processed
            metadata = {
                "processed": "true",
                "processed_at": datetime.now(UTC).isoformat(),
            }
            success = await self.azure_blob_manager.set_blob_metadata(blob_name=blob_path, metadata=metadata)
            if success:
                logger.info(f"Marked blob as processed: {blob_path}")
            else:
                logger.warning(f"Failed to mark blob as processed: {blob_path}")

            delete_success = await self.azure_blob_manager.delete_blob(blob_path)
            if delete_success:
                logger.info(f"Successfully deleted blob: {blob_path}")
            else:
                logger.warning(f"Failed to delete blob: {blob_path}")

        except Exception as e:
            logger.error(f"Error marking blob as processed and deleting {blob_path}: {e}")

    async def _mark_blob_with_error(self, blob_path: str, error_message: str) -> None:
        """
        Mark a blob with error information and increment retry count.

        Parameters
        ----------
        blob_path : str
            The blob path.
        error_message : str
            The error message to store.
        """
        try:
            # Get current metadata to preserve retry count
            current_metadata = await self.azure_blob_manager.get_blob_metadata(blob_path) or {}
            current_retry_count = int(current_metadata.get("retry_count", "0"))
            new_retry_count = current_retry_count + 1

            metadata = {
                "processed": "false",
                "retry_count": str(new_retry_count),
                "last_attempt": datetime.now(UTC).isoformat(),
                "last_error": error_message[:1000],  # Limit error message length
                "status": "retrying",  # Will be retried on next poll
            }
            await self.azure_blob_manager.set_blob_metadata(blob_name=blob_path, metadata=metadata)
            logger.info(f"User {self.user_email}: Marked blob with error (attempt {new_retry_count}): {blob_path}")
        except Exception as e:
            logger.error(f"User {self.user_email}: Error marking blob with error {blob_path}: {e}")

    async def _mark_blob_permanently_failed(self, blob_path: str, current_metadata: dict) -> None:
        """
        Mark a blob as permanently failed after exceeding retry limit.

        Parameters
        ----------
        blob_path : str
            The blob path.
        current_metadata : dict
            Current metadata from the blob.
        """
        try:
            metadata = {
                "processed": "false",
                "status": "permanently_failed",
                "retry_count": current_metadata.get("retry_count", "0"),
                "last_attempt": datetime.now(UTC).isoformat(),
                "last_error": current_metadata.get("last_error", "Max retries exceeded"),
                "failed_at": datetime.now(UTC).isoformat(),
            }
            await self.azure_blob_manager.set_blob_metadata(blob_name=blob_path, metadata=metadata)
            logger.error(
                f"User {self.user_email}: Marked blob as permanently failed after "
                f"{current_metadata.get('retry_count', 0)} attempts: {blob_path}"
            )
        except Exception as e:
            logger.error(f"User {self.user_email}: Error marking blob as permanently failed {blob_path}: {e}")

    def _should_delete_old_blob(self, metadata: dict) -> tuple[bool, str]:
        """
        Determine if an old blob should be deleted during startup cleanup.

        Parameters
        ----------
        metadata : dict
            The blob's metadata dictionary.

        Returns
        -------
        tuple[bool, str]
            (should_delete, reason) - True if should delete, with reason for logging.
        """
        # Case 1: Successfully processed blobs - safe to delete
        if metadata.get("processed") == "true":
            return True, "successfully processed"

        # Case 2: Legacy blob without metadata - delete for data protection
        # These are pre-migration blobs that never had metadata tracking
        if not metadata or ("processed" not in metadata and "retry_count" not in metadata and "status" not in metadata):
            return True, "legacy blob without metadata"

        # Case 3: Blob with retry metadata - keep for processing/investigation
        status = metadata.get("status", "unknown")
        retry_count = metadata.get("retry_count", "0")
        return False, f"has metadata (status={status}, retry_count={retry_count})"

    def _evaluate_blob_for_cleanup(self, blob: dict) -> tuple[bool, str | None]:
        """
        Evaluate if a blob should be included in cleanup.

        Parameters
        ----------
        blob : dict
            Blob information dictionary.

        Returns
        -------
        tuple[bool, str | None]
            (should_cleanup, reason) - True if should delete, reason for logging or None to skip.
        """
        blob_name = blob["name"]

        # Security check
        if not blob_name.startswith(self.user_uploads_prefix):
            logger.error(
                f"Security check failed during cleanup: Blob '{blob_name}' does not match "
                f"user prefix '{self.user_uploads_prefix}' for user {self.user_email}"
            )
            return False, None

        # Only consider audio files
        blob_path = Path(blob_name)
        if blob_path.suffix.lower() not in self.supported_extensions:
            return False, None

        # Check if blob is old
        # last_modified = blob.get("last_modified")
        # if not (last_modified and last_modified < self.startup_time):
        #     return False, None

        # Determine if this old blob should be deleted based on metadata
        metadata = blob.get("metadata", {})
        should_delete, reason = self._should_delete_old_blob(metadata)
        return should_delete, reason

    async def _cleanup_old_blobs_on_startup(self) -> None:
        """
        Clean up this user's blobs older than the service startup time.

        This runs once on the first poll to:
        1. Remove old recordings for this user that should have been cleaned up
        2. Ensure we only work with new uploads from this session

        Includes defensive checks to ensure only this user's blobs are deleted.
        """
        try:
            logger.info(f"User {self.user_email}: Starting cleanup of old blobs from before service startup...")

            # List all blobs with user-specific prefix
            all_blobs = await self.azure_blob_manager.list_blobs_in_prefix(
                prefix=self.user_uploads_prefix, include_metadata=True
            )

            # Evaluate blobs for cleanup
            old_blobs = []
            for blob in all_blobs:
                should_delete, reason = self._evaluate_blob_for_cleanup(blob)

                if reason is None:  # Skip blobs that don't meet criteria
                    continue

                blob_name = blob["name"]
                if should_delete:
                    old_blobs.append(blob)
                    logger.info(f"User {self.user_email}: Will clean up old blob ({reason}): {blob_name}")
                else:
                    logger.info(f"User {self.user_email}: Keeping old blob ({reason}): {blob_name}")

            if old_blobs:
                logger.info(f"User {self.user_email}: Found {len(old_blobs)} old blob(s) to clean up")

                # Delete each old blob
                for blob in old_blobs:
                    blob_name = blob["name"]
                    try:
                        success = await self.azure_blob_manager.delete_blob(blob_name)
                        if success:
                            logger.info(f"User {self.user_email}: Deleted old blob: {blob_name}")
                        else:
                            logger.warning(f"User {self.user_email}: Failed to delete old blob: {blob_name}")
                    except Exception as e:
                        logger.error(f"User {self.user_email}: Error deleting old blob {blob_name}: {e}")

                logger.info(f"User {self.user_email}: Cleanup complete - processed {len(old_blobs)} old blob(s)")
            else:
                logger.info(f"User {self.user_email}: No old blobs found to clean up")

        except Exception as e:
            logger.error(f"User {self.user_email}: Error during startup cleanup: {e}")

    async def run_polling_loop(self) -> None:
        """
        Run the continuous polling loop for this user.

        This method runs indefinitely, polling for new audio files every
        30 seconds and processing them for this user only.

        On the first poll, it cleans up any of this user's blobs older than
        the service startup time.
        """
        logger.info(
            f"User {self.user_email}: Starting transcription polling service "
            f"(interval: {self.polling_interval_seconds}s)"
        )

        while True:
            try:
                # On first poll, clean up old blobs for this user
                if self._is_first_poll:
                    await self._cleanup_old_blobs_on_startup()
                    self._is_first_poll = False

                # Poll for new files
                unprocessed_files = await self.poll_for_new_audio_files()

                # Process each file
                for blob_info in unprocessed_files:
                    try:
                        await self.process_discovered_audio(blob_info)
                    except Exception as e:
                        logger.error(
                            f"User {self.user_email}: Error processing blob " f"{blob_info.get('name', 'unknown')}: {e}"
                        )
                        # Continue processing other files even if one fails

            except Exception as e:
                logger.error(f"User {self.user_email}: Error in polling loop: {e}")

            # Wait before next poll
            await asyncio.sleep(self.polling_interval_seconds)
