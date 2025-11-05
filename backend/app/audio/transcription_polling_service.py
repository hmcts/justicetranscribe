"""
Transcription Polling Service for automatic audio file discovery and processing.

This service polls Azure Blob Storage for new audio files and automatically triggers
transcription processing without requiring frontend API calls. This avoids JWT timeout
issues on long audio recordings.
"""

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import sentry_sdk
from sqlmodel import select

from app.audio.azure_utils import AsyncAzureBlobManager
from app.audio.process_audio_fully import transcribe_and_generate_llm_output
from app.audio.utils import extract_transcription_id_from_blob_path
from app.database.connection import get_async_session
from app.database.postgres_models import (
    BlobProcessingAttempt,
    Transcription,
    TranscriptionJob,
    User,
)
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
        self.min_blob_path_parts = 3  # Minimum parts for valid path: "user-uploads/email/filename"
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
        last_modified = blob.get("last_modified")
        if last_modified and last_modified < self.startup_time:
            return True

        # Check metadata for processing status
        metadata = blob.get("metadata", {})

        # Skip if already successfully processed
        if metadata.get("processed") == "true":
            return True

        # Skip if permanently failed
        if metadata.get("status") == "permanently_failed":
            logger.debug(
                f"User {self.user_email}: Skipping permanently failed blob: {blob_name}"
            )
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
                logger.info(
                    f"User {self.user_email}: Found {len(unprocessed)} unprocessed audio files"
                )

        except Exception as e:
            logger.error(
                f"User {self.user_email}: Error polling for new audio files: {e}"
            )
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
            logger.error(
                f"User {self.user_email}: Error extracting email from blob path '{blob_path}': {e}"
            )

        return None

    async def get_or_create_user_by_email(self, email: str) -> User | None:
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
            async with get_async_session() as session:
                statement = select(User).where(User.email == email)
                result = await session.execute(statement)
                user = result.scalar_one_or_none()

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
        logger.info(
            f"User {self.user_email}: Processing discovered audio file: {blob_path}"
        )

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
                error_msg = (
                    f"Could not extract/validate user email from blob path: {blob_path}"
                )
                logger.error(f"User {self.user_email}: {error_msg}")
                await self._mark_blob_with_error(blob_path, error_msg)
                return False

            # Look up user in database
            user = await self.get_or_create_user_by_email(user_email)
            if not user:
                error_msg = f"User not found for email: {user_email}"
                logger.error(f"User {self.user_email}: {error_msg}")
                await self._mark_blob_with_error(blob_path, error_msg)
                return False

            # Trigger transcription processing
            transcription_id = extract_transcription_id_from_blob_path(
                blob_path, self.user_email
            )

            logger.info(
                f"User {self.user_email}: Starting transcription for blob: {blob_path}"
            )

            await transcribe_and_generate_llm_output(
                user_upload_blob_storage_file_key=blob_path,
                user_id=user.id,
                user_email=user.email,
                transcription_id=transcription_id,
            )

            # Mark blob as processed
            await self._mark_blob_as_processed_and_soft_delete(blob_path)

            logger.info(
                f"User {self.user_email}: Successfully processed audio file: {blob_path}"
            )

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
            success = await self.azure_blob_manager.set_blob_metadata(
                blob_name=blob_path, metadata=metadata
            )
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
            logger.error(
                f"Error marking blob as processed and deleting {blob_path}: {e}"
            )

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
            current_metadata = (
                await self.azure_blob_manager.get_blob_metadata(blob_path) or {}
            )
            current_retry_count = int(current_metadata.get("retry_count", "0"))
            new_retry_count = current_retry_count + 1

            metadata = {
                "processed": "false",
                "retry_count": str(new_retry_count),
                "last_attempt": datetime.now(UTC).isoformat(),
                "last_error": error_message[:1000],  # Limit error message length
                "status": "retrying",  # Will be retried on next poll
            }
            await self.azure_blob_manager.set_blob_metadata(
                blob_name=blob_path, metadata=metadata
            )
            logger.info(
                f"User {self.user_email}: Marked blob with error (attempt {new_retry_count}): {blob_path}"
            )
        except Exception as e:
            logger.error(
                f"User {self.user_email}: Error marking blob with error {blob_path}: {e}"
            )

    async def _mark_blob_permanently_failed(
        self, blob_path: str, current_metadata: dict
    ) -> None:
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
                "last_error": current_metadata.get(
                    "last_error", "Max retries exceeded"
                ),
                "failed_at": datetime.now(UTC).isoformat(),
            }
            await self.azure_blob_manager.set_blob_metadata(
                blob_name=blob_path, metadata=metadata
            )
            logger.error(
                f"User {self.user_email}: Marked blob as permanently failed after "
                f"{current_metadata.get('retry_count', 0)} attempts: {blob_path}"
            )
        except Exception as e:
            logger.error(
                f"User {self.user_email}: Error marking blob as permanently failed {blob_path}: {e}"
            )

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
        if not metadata or (
            "processed" not in metadata
            and "retry_count" not in metadata
            and "status" not in metadata
        ):
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
        last_modified = blob.get("last_modified")
        if not (last_modified and last_modified < self.startup_time):
            return False, None

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
            logger.info(
                f"User {self.user_email}: Starting cleanup of old blobs from before service startup..."
            )

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
                    logger.info(
                        f"User {self.user_email}: Will clean up old blob ({reason}): {blob_name}"
                    )
                else:
                    logger.info(
                        f"User {self.user_email}: Keeping old blob ({reason}): {blob_name}"
                    )

            if old_blobs:
                logger.info(
                    f"User {self.user_email}: Found {len(old_blobs)} old blob(s) to clean up"
                )

                # Delete each old blob
                for blob in old_blobs:
                    blob_name = blob["name"]
                    try:
                        success = await self.azure_blob_manager.delete_blob(blob_name)
                        if success:
                            logger.info(
                                f"User {self.user_email}: Deleted old blob: {blob_name}"
                            )
                        else:
                            logger.warning(
                                f"User {self.user_email}: Failed to delete old blob: {blob_name}"
                            )
                    except Exception as e:
                        logger.error(
                            f"User {self.user_email}: Error deleting old blob {blob_name}: {e}"
                        )

                logger.info(
                    f"User {self.user_email}: Cleanup complete - processed {len(old_blobs)} old blob(s)"
                )
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
                            f"User {self.user_email}: Error processing blob "
                            f"{blob_info.get('name', 'unknown')}: {e}"
                        )
                        # Continue processing other files even if one fails

            except Exception as e:
                logger.error(f"User {self.user_email}: Error in polling loop: {e}")

            # Wait before next poll
            await asyncio.sleep(self.polling_interval_seconds)


class GlobalTranscriptionPollingService:
    """
    Global service for polling Azure Blob Storage and processing audio files for all users.

    Polls the entire user-uploads/ prefix every 30 seconds and processes discovered
    blobs concurrently (up to 10 at a time). Uses TranscriptionJob existence as the
    source of truth for whether a blob has been processed.
    """

    # Class constants
    MAX_RETRY_ATTEMPTS = 2  # Maximum processing attempts before marking as permanently failed
    MAX_CONCURRENT_PROCESSING = 10  # Maximum concurrent blob processing operations
    POLLING_INTERVAL_SECONDS = 30  # Time between polling cycles

    def __init__(self):
        """
        Initialize the global transcription polling service.

        Sets up Azure blob manager, polling parameters, and concurrency limits.
        """
        self.settings = get_settings()
        self.azure_blob_manager = AsyncAzureBlobManager()
        self.user_uploads_prefix = "user-uploads/"
        self.supported_extensions = {".mp4", ".webm", ".wav", ".m4a"}
        self.min_blob_path_parts = 3  # Minimum parts for valid path: "user-uploads/email/filename"
        self._polling_in_progress = False  # Prevent overlapping poll cycles
        logger.info("Global transcription polling service initialized")

    async def _delete_blob_and_return_true(self, blob_path: str, reason: str) -> bool:
        """
        Helper to delete a blob and return True (processed/skip signal).

        Parameters
        ----------
        blob_path : str
            The blob path to delete.
        reason : str
            Log message explaining why blob is being deleted.

        Returns
        -------
        bool
            Always returns True to signal blob should be skipped.
        """
        logger.warning(f"✓ {reason}: {blob_path}. Deleting immediately.")
        await self.azure_blob_manager.delete_blob(blob_path)
        logger.info(f"Deleted blob: {blob_path}")
        return True

    async def blob_has_been_processed(self, blob_path: str, blob_metadata: dict) -> bool:
        """
        Check if a blob has been processed or should be deleted.

        Checks multiple signals and deletes blobs immediately when appropriate:
        0. Blob metadata status is "permanently_failed" → Delete immediately
        1. Blob metadata retry_count >= MAX_RETRY_ATTEMPTS (legacy from old system) → Delete immediately
        2. TranscriptionJob exists (successful processing) → Delete immediately (orphaned blob)
        3. Transcription record exists (failed early) → Delete immediately (prevents untitled meetings)
        4. BlobProcessingAttempt count >= MAX_RETRY_ATTEMPTS (retry limit) → Already deleted, skip

        Parameters
        ----------
        blob_path : str
            The full blob path to check.
        blob_metadata : dict
            The blob's metadata dictionary.

        Returns
        -------
        bool
            True if blob should be skipped (already processed, deleted, or awaiting deletion).
        """
        try:
            # Check 0: Blob metadata shows permanently_failed status
            if blob_metadata.get("status") == "permanently_failed":
                return await self._delete_blob_and_return_true(
                    blob_path, "Found blob marked permanently_failed but not deleted"
                )

            # Check 1: Legacy blob with high retry count from old system
            try:
                metadata_retry_count = int(blob_metadata.get("retry_count", "0"))
                if metadata_retry_count >= self.MAX_RETRY_ATTEMPTS:
                    return await self._delete_blob_and_return_true(
                        blob_path, f"Found legacy blob with retry_count={metadata_retry_count}"
                    )
            except (ValueError, TypeError):
                pass  # Invalid retry_count format, ignore

            async with get_async_session() as session:
                # Check 2: TranscriptionJob exists - orphaned blob, delete it
                job_statement = select(TranscriptionJob).where(
                    TranscriptionJob.s3_audio_url == blob_path
                )
                result = await session.execute(job_statement)
                if result.scalar_one_or_none() is not None:
                    return await self._delete_blob_and_return_true(
                        blob_path, "Found orphaned blob (TranscriptionJob exists but blob not deleted)"
                    )

                # Check 3: Transcription record exists (failed early) - delete to prevent untitled meetings
                try:
                    filename = Path(blob_path).stem
                    from uuid import UUID
                    UUID(filename)  # Validate it's a UUID

                    trans_statement = select(Transcription).where(Transcription.id == filename)
                    result = await session.execute(trans_statement)
                    if result.scalar_one_or_none() is not None:
                        return await self._delete_blob_and_return_true(
                            blob_path, "Found blob with Transcription but no TranscriptionJob (failed early)"
                        )
                except (ValueError, AttributeError):
                    pass  # Not a valid UUID filename, can't check by ID

                # Check 4: PostgreSQL-tracked attempt count - skip if >= MAX_RETRY_ATTEMPTS
                attempt_statement = select(BlobProcessingAttempt).where(
                    BlobProcessingAttempt.blob_path == blob_path
                )
                result = await session.execute(attempt_statement)
                attempt = result.scalar_one_or_none()
                if attempt and attempt.attempt_count >= self.MAX_RETRY_ATTEMPTS:
                    logger.warning(
                        f"✓ Skipping blob (exceeded retry limit: {attempt.attempt_count} attempts): {blob_path}. "
                        f"Last error: {attempt.last_error}"
                    )
                    return True

        except Exception as e:
            logger.error(f"Error checking if blob processed {blob_path}: {e}")

        # Default: blob not processed, should be processed
        return False

    async def _filter_candidate_blobs(self, all_blobs: list[dict]) -> list[dict]:
        """
        Filter blobs by extension and metadata signals (no DB query).

        Parameters
        ----------
        all_blobs : list[dict]
            All blobs from Azure Storage.

        Returns
        -------
        list[dict]
            Blobs that pass extension and metadata checks.
        """
        candidate_blobs = []
        for blob in all_blobs:
            blob_name = blob["name"]
            blob_metadata = blob.get("metadata", {})

            # Check extension
            if Path(blob_name).suffix.lower() not in self.supported_extensions:
                continue

            # Check metadata-only signals (no DB query needed)
            if blob_metadata.get("status") == "permanently_failed":
                logger.warning(f"Found orphaned permanently_failed blob: {blob_name}, deleting")
                await self.azure_blob_manager.delete_blob(blob_name)
                continue

            # Check for legacy high-retry blobs from old system
            try:
                metadata_retry_count = int(blob_metadata.get("retry_count", "0"))
                if metadata_retry_count >= self.MAX_RETRY_ATTEMPTS:
                    logger.warning(f"Found legacy blob with retry_count={metadata_retry_count}: {blob_name}, deleting")
                    await self.azure_blob_manager.delete_blob(blob_name)
                    continue
            except (ValueError, TypeError):
                pass

            candidate_blobs.append(blob)

        return candidate_blobs

    async def _get_processed_and_failed_paths(self, candidate_blobs: list[dict]) -> tuple[set[str], set[str]]:
        """
        Execute batched database queries to find processed and failed-early blobs.

        Parameters
        ----------
        candidate_blobs : list[dict]
            Candidate blobs to check.

        Returns
        -------
        tuple[set[str], set[str]]
            (processed_paths, failed_early_ids) - Sets of blob paths/IDs to skip.
        """
        blob_paths = [blob["name"] for blob in candidate_blobs]

        async with get_async_session() as session:
            # Query 1: Get all TranscriptionJobs for these blobs
            job_statement = select(TranscriptionJob.s3_audio_url).where(
                TranscriptionJob.s3_audio_url.in_(blob_paths)
            )
            result = await session.execute(job_statement)
            processed_paths = set(result.scalars().all())

            # Query 2: Get all Transcriptions for blob filenames
            potential_transcription_ids = []
            for blob in candidate_blobs:
                try:
                    filename = Path(blob["name"]).stem
                    from uuid import UUID
                    UUID(filename)  # Validate it's a UUID
                    potential_transcription_ids.append(filename)
                except (ValueError, TypeError):
                    pass

            failed_early_ids = set()
            if potential_transcription_ids:
                trans_statement = select(Transcription.id).where(
                    Transcription.id.in_(potential_transcription_ids)
                )
                result = await session.execute(trans_statement)
                failed_early_ids = {str(t) for t in result.scalars().all()}

        return processed_paths, failed_early_ids

    async def poll_for_unprocessed_blobs(self) -> list[dict]:
        """
        Poll entire user-uploads/ prefix for blobs that need processing.

        Uses BATCHED database queries for efficiency at scale.

        Returns blobs that:
        - Have supported audio extension
        - Have NOT been processed (checks TranscriptionJob, Transcription, and metadata retry count)

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
            # Step 1: List all blobs
            all_blobs = await self.azure_blob_manager.list_blobs_in_prefix(
                prefix=self.user_uploads_prefix,
                include_metadata=True
            )
            logger.info(
                f"Listed {len(all_blobs)} blobs with prefix '{self.user_uploads_prefix}' "
                f"in container '{self.azure_blob_manager.container_name}'"
            )

            # Step 2: Filter by extension and metadata (no DB queries)
            candidate_blobs = await self._filter_candidate_blobs(all_blobs)
            if not candidate_blobs:
                return []

            # Step 3: Batch DB queries to find processed/failed blobs
            processed_paths, failed_early_ids = await self._get_processed_and_failed_paths(candidate_blobs)

            # Step 4: Filter out processed/failed blobs, delete orphaned ones
            unprocessed = []
            for blob in candidate_blobs:
                blob_name = blob["name"]

                # Orphaned blob (successfully processed but not deleted)
                if blob_name in processed_paths:
                    logger.warning(f"✓ Found orphaned blob: {blob_name}. Deleting immediately.")
                    await self.azure_blob_manager.delete_blob(blob_name)
                    continue

                # Failed-early blob (Transcription exists but no TranscriptionJob)
                filename = Path(blob_name).stem
                if filename in failed_early_ids:
                    logger.warning(f"✓ Found failed-early blob: {blob_name}. Deleting to prevent untitled meeting.")
                    await self.azure_blob_manager.delete_blob(blob_name)
                    continue

                unprocessed.append(blob)

            # Return empty list or log and return unprocessed blobs
            if not unprocessed:
                return []
            else:
                logger.info(f"Global polling: Found {len(unprocessed)} unprocessed blobs")
                return unprocessed

        except Exception as e:
            logger.error(f"Global polling: Error polling for blobs: {e}")
            return []

    def extract_user_email_from_blob_path(self, blob_path: str) -> str | None:
        """
        Extract user email from user-uploads/{email}/{filename} path.

        Parameters
        ----------
        blob_path : str
            The full blob path.

        Returns
        -------
        str | None
            The user email if successfully extracted, None otherwise.
        """
        try:
            parts = blob_path.split("/")
            if len(parts) >= self.min_blob_path_parts and parts[0] == "user-uploads":
                return parts[1]
        except Exception as e:
            logger.error(f"Error extracting email from blob path '{blob_path}': {e}")
        return None

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Look up user by email in the database (case-insensitive).

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
            # Normalize email to lowercase for case-insensitive lookup
            normalized_email = email.lower()

            async with get_async_session() as session:
                statement = select(User).where(User.email == normalized_email)
                result = await session.execute(statement)
                user = result.scalar_one_or_none()

                if not user:
                    # Try original case as fallback (in case DB has mixed case)
                    statement = select(User).where(User.email == email)
                    result = await session.execute(statement)
                    user = result.scalar_one_or_none()

                    if user:
                        logger.warning(
                            f"Found user with original case '{email}' but not normalized case. "
                            f"Consider normalizing emails in database."
                        )

                return user
        except Exception as e:
            logger.error(f"Error looking up user by email '{email}': {e}")
            return None

    async def process_single_blob(self, blob_info: dict) -> bool:
        """
        Process a single discovered blob.

        Writes metadata for troubleshooting and tracks attempts in PostgreSQL.

        Parameters
        ----------
        blob_info : dict
            Dictionary containing blob information from poll_for_unprocessed_blobs.

        Returns
        -------
        bool
            True if processing was successful, False otherwise.
        """
        blob_path = blob_info["name"]
        logger.info(f"Global polling: Processing blob: {blob_path}")

        try:
            # Extract user email
            user_email = self.extract_user_email_from_blob_path(blob_path)
            if not user_email:
                error_msg = f"Could not extract user email from blob path: {blob_path}"
                logger.error(error_msg)
                await self._record_processing_attempt(blob_path, error_msg)
                await self._write_metadata_for_troubleshooting(
                    blob_path, status="error", error=error_msg
                )
                return False

            # Look up user
            user = await self.get_user_by_email(user_email)
            if not user:
                error_msg = f"User not found for email: {user_email}"
                logger.error(error_msg)
                await self._record_processing_attempt(blob_path, error_msg)
                await self._write_metadata_for_troubleshooting(
                    blob_path, status="error", error=error_msg
                )
                return False

            # Trigger transcription
            transcription_id = extract_transcription_id_from_blob_path(
                blob_path, user_email
            )

            logger.info(f"Starting transcription for blob: {blob_path}")

            await transcribe_and_generate_llm_output(
                user_upload_blob_storage_file_key=blob_path,
                user_id=user.id,
                user_email=user.email,
                transcription_id=transcription_id,
            )

            # Mark as processed and delete blob
            await self._mark_processed_and_delete(blob_path)

        except Exception as e:
            error_msg = f"Error processing blob {blob_path}: {e}"
            logger.error(error_msg)

            # Record the attempt and check if we've hit the retry limit
            attempt_count = await self._record_processing_attempt(blob_path, str(e))

            if attempt_count >= self.MAX_RETRY_ATTEMPTS:
                # Hit retry limit - delete blob immediately
                logger.warning(
                    f"Blob has reached retry limit ({attempt_count} attempts): {blob_path}. "
                    f"Deleting immediately. Last error: {e!s}"
                )
                try:
                    await self.azure_blob_manager.delete_blob(blob_path)
                    logger.info(f"Deleted permanently failed blob: {blob_path}")

                    # Clean up BlobProcessingAttempt record to prevent database bloat
                    await self._delete_processing_attempt_record(blob_path)
                except Exception as delete_error:
                    logger.error(f"Failed to delete blob {blob_path}: {delete_error}")
            else:
                # Still under retry limit - write metadata for troubleshooting
                await self._write_metadata_for_troubleshooting(
                    blob_path, status="retrying", error=str(e)
                )

            return False

        else:
            # Success: processing completed without exceptions
            logger.info(f"Successfully processed blob: {blob_path}")
            return True

    async def _record_processing_attempt(self, blob_path: str, error: str | None = None) -> int:
        """
        Record a processing attempt in PostgreSQL.

        This is the source of truth for retry logic (not blob metadata).

        Parameters
        ----------
        blob_path : str
            The blob path.
        error : str | None
            Optional error message to store.

        Returns
        -------
        int
            The new attempt count after recording this attempt.

        Raises
        ------
        Exception
            Re-raises any database exceptions to signal critical failure.
        """
        try:
            async with get_async_session() as session:
                # Get or create attempt record
                statement = select(BlobProcessingAttempt).where(
                    BlobProcessingAttempt.blob_path == blob_path
                )
                result = await session.execute(statement)
                attempt = result.scalar_one_or_none()

                if not attempt:
                    # Create new attempt record (attempt_count starts at default 0)
                    attempt = BlobProcessingAttempt(
                        blob_path=blob_path,
                        last_error=error[:1000] if error else None,
                        last_attempt_at=datetime.now(UTC),
                    )
                    session.add(attempt)
                else:
                    # Update existing record
                    attempt.last_error = error[:1000] if error else None
                    attempt.last_attempt_at = datetime.now(UTC)

                # Increment attempt count (0→1 on first attempt, 1→2 on second, etc.)
                attempt.attempt_count += 1

                # Commit happens automatically in get_async_session context manager
                logger.debug(
                    f"Recorded processing attempt {attempt.attempt_count} for {blob_path}"
                )

                return attempt.attempt_count

        except Exception as e:
            logger.critical(f"Database error recording processing attempt for {blob_path}: {e}")
            # Re-raise to trigger circuit breaker in polling loop
            raise

    async def _delete_processing_attempt_record(self, blob_path: str) -> None:
        """
        Delete the BlobProcessingAttempt record for a blob.

        Called after successful processing or when hitting retry limit to prevent
        database bloat from accumulating records indefinitely.

        Parameters
        ----------
        blob_path : str
            The blob path.
        """
        try:
            async with get_async_session() as session:
                statement = select(BlobProcessingAttempt).where(
                    BlobProcessingAttempt.blob_path == blob_path
                )
                result = await session.execute(statement)
                attempt = result.scalar_one_or_none()

                if attempt:
                    session.delete(attempt)
                    # Commit happens automatically in get_async_session context manager
                    logger.debug(f"Deleted BlobProcessingAttempt record for {blob_path}")
                else:
                    logger.debug(f"No BlobProcessingAttempt record found for {blob_path}")

        except Exception as e:
            logger.warning(
                f"Failed to delete BlobProcessingAttempt record for {blob_path}: {e}. "
                "This may cause minor database bloat but does not affect functionality."
            )

    async def _write_metadata_for_troubleshooting(
        self, blob_path: str, status: str, error: str | None = None
    ) -> None:
        """
        Write metadata to blob for troubleshooting purposes only.

        This metadata is NOT used for control flow or retry logic.
        PostgreSQL (BlobProcessingAttempt) is the source of truth.

        Metadata persists even after soft-delete, allowing debugging via Azure Portal
        by restoring blob to current version and inspecting metadata.

        Parameters
        ----------
        blob_path : str
            The blob path.
        status : str
            The status to write (e.g., "error", "retrying").
        error : str | None
            Optional error message to include.
        """
        try:
            current_metadata = await self.azure_blob_manager.get_blob_metadata(blob_path) or {}
            retry_count = int(current_metadata.get("retry_count", "0")) + 1

            metadata = {
                "status": status,
                "retry_count": str(retry_count),
                "last_attempt": datetime.now(UTC).isoformat(),
            }

            if error:
                metadata["last_error"] = error[:1000]

            await self.azure_blob_manager.set_blob_metadata(
                blob_name=blob_path, metadata=metadata
            )
        except Exception as e:
            logger.warning(f"Failed to write troubleshooting metadata for {blob_path}: {e}")

    async def _mark_processed_and_delete(self, blob_path: str) -> None:
        """
        Mark blob as processed and delete it.

        Writes metadata before deletion so it persists on soft-deleted blob
        for debugging purposes (can restore and inspect via Azure Portal).
        Also deletes the corresponding BlobProcessingAttempt record to prevent
        database bloat.

        Parameters
        ----------
        blob_path : str
            The blob path.
        """
        try:
            # Write metadata for troubleshooting (persists after soft-delete)
            metadata = {
                "processed": "true",
                "processed_at": datetime.now(UTC).isoformat(),
            }
            await self.azure_blob_manager.set_blob_metadata(
                blob_name=blob_path, metadata=metadata
            )

            # Delete blob (soft delete - metadata persists for 7 days)
            await self.azure_blob_manager.delete_blob(blob_path)
            logger.info(f"Deleted processed blob: {blob_path}")

            # Clean up BlobProcessingAttempt record to prevent database bloat
            await self._delete_processing_attempt_record(blob_path)

        except Exception as e:
            logger.error(f"Error marking/deleting blob {blob_path}: {e}")

    def _is_database_error(self, error: Exception) -> bool:
        """
        Check if an exception is database-related.

        Parameters
        ----------
        error : Exception
            The exception to check.

        Returns
        -------
        bool
            True if error appears to be database-related.
        """
        error_str = str(error).lower()
        db_keywords = ["database", "connection", "postgres", "sqlalchemy"]
        return any(keyword in error_str for keyword in db_keywords)

    def _handle_database_failure(
        self, error: Exception, consecutive_failures: int, max_failures: int
    ) -> tuple[bool, int]:
        """
        Handle database failure and determine if polling should stop.

        Parameters
        ----------
        error : Exception
            The database error that occurred.
        consecutive_failures : int
            Current count of consecutive database failures.
        max_failures : int
            Maximum allowed consecutive failures.

        Returns
        -------
        tuple[bool, int]
            (should_stop_polling, new_failure_count)
        """
        new_count = consecutive_failures + 1
        logger.critical(
            f"🔴 PostgreSQL error in polling loop ({new_count}/{max_failures}): {error}"
        )
        sentry_sdk.capture_exception(error)

        if new_count >= max_failures:
            critical_msg = (
                f"PostgreSQL unreachable after {max_failures} consecutive attempts. "
                "STOPPING GLOBAL POLLING SERVICE. Manual restart required."
            )
            logger.critical(f"🛑 {critical_msg}")
            sentry_sdk.capture_message(critical_msg, level="fatal")
            return True, new_count

        return False, new_count

    async def _process_blobs_concurrently(
        self, unprocessed_blobs: list[dict]
    ) -> int:
        """
        Process multiple blobs concurrently with semaphore limit.

        Parameters
        ----------
        unprocessed_blobs : list[dict]
            List of blob info dictionaries to process.

        Returns
        -------
        int
            Number of blobs successfully processed.
        """
        processed_count = 0
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_PROCESSING)

        async def process_with_semaphore(blob_info, sem=semaphore):
            nonlocal processed_count
            async with sem:
                try:
                    success = await self.process_single_blob(blob_info)
                    if success:
                        processed_count += 1
                except Exception as e:
                    # Check if it's a database error
                    if self._is_database_error(e):
                        logger.critical(f"Database error during blob processing: {e}")
                        sentry_sdk.capture_exception(e)
                        raise

                    logger.error(f"Non-database error processing blob: {e}")
                    sentry_sdk.capture_exception(e)

        # Process all blobs concurrently (limited by semaphore)
        results = await asyncio.gather(
            *[process_with_semaphore(blob) for blob in unprocessed_blobs],
            return_exceptions=True
        )

        # Check for database exceptions in results - they need to propagate
        # to trigger the circuit breaker in run_polling_loop
        for result in results:
            if isinstance(result, Exception) and self._is_database_error(result):
                logger.critical(
                    f"Database error detected in concurrent processing results: {result}"
                )
                raise result

        return processed_count

    async def run_polling_loop(self) -> None:
        """
        Main polling loop: scan all user uploads every 30s, process up to 10 concurrently.

        This method runs indefinitely, polling for unprocessed blobs across all users
        and processing them with a concurrency limit. Failed blobs are deleted immediately
        upon hitting the retry limit.

        Includes overlapping poll prevention, performance metrics logging, and circuit
        breaker for PostgreSQL failures (stops polling after 3 consecutive DB errors).
        """
        import time

        logger.info(
            f"Starting global transcription polling service "
            f"(interval: {self.POLLING_INTERVAL_SECONDS}s, "
            f"max concurrent: {self.MAX_CONCURRENT_PROCESSING})"
        )

        consecutive_db_failures = 0
        max_db_failures = 3

        while True:
            # Prevent overlapping poll cycles
            if self._polling_in_progress:
                logger.warning(
                    "⚠️ Previous poll cycle still in progress, skipping this cycle. "
                    "Consider increasing concurrency or reducing poll interval."
                )
                await asyncio.sleep(self.POLLING_INTERVAL_SECONDS)
                continue

            self._polling_in_progress = True
            poll_start_time = time.time()
            processed_count = 0
            total_blob_count = 0

            try:
                # Find unprocessed blobs
                unprocessed_blobs = await self.poll_for_unprocessed_blobs()
                total_blob_count = len(unprocessed_blobs)

                if unprocessed_blobs:
                    # Process with concurrency limit
                    processed_count = await self._process_blobs_concurrently(unprocessed_blobs)

                # Success: reset failure counter
                consecutive_db_failures = 0

            except Exception as e:
                # Check if this is a database-related error
                if self._is_database_error(e):
                    should_stop, consecutive_db_failures = self._handle_database_failure(
                        e, consecutive_db_failures, max_db_failures
                    )
                    if should_stop:
                        break  # Exit polling loop entirely
                else:
                    # Non-database error, log but continue
                    logger.error(f"Error in global polling loop: {e}")
                    sentry_sdk.capture_exception(e)
                    consecutive_db_failures = 0  # Reset counter for non-DB errors

            finally:
                self._polling_in_progress = False
                poll_duration = time.time() - poll_start_time

                # Log poll cycle metrics
                logger.info(
                    f"📊 Poll cycle complete: "
                    f"duration={poll_duration:.2f}s, "
                    f"found={total_blob_count}, "
                    f"processed={processed_count}"
                )

                # Alert if poll cycle is getting close to interval duration
                if poll_duration > (self.POLLING_INTERVAL_SECONDS * 0.8):
                    logger.warning(
                        f"⚠️ Poll cycle took {poll_duration:.2f}s "
                        f"({poll_duration/self.POLLING_INTERVAL_SECONDS*100:.0f}% of {self.POLLING_INTERVAL_SECONDS}s interval). "
                        f"Consider scaling optimizations if this persists."
                    )

            # Wait before next poll
            await asyncio.sleep(self.POLLING_INTERVAL_SECONDS)

        # If we reach here, polling stopped due to critical failure
        logger.critical("Global transcription polling service has been stopped.")
