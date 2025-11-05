from datetime import UTC, datetime
from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from sqlalchemy import Column, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field, Relationship, SQLModel

# Global config for all models
model_config = {
    "from_attributes": True,
    "extra": "ignore",
    "use_enum_values": True,
}


class TemplateName(str, Enum):
    GENERAL = "General"
    CRISSA = "Crissa"


class BaseTable(SQLModel):
    model_config = {  # noqa: RUF012
        "from_attributes": True,
    }

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    created_datetime: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_datetime: datetime | None = Field(default_factory=lambda: datetime.now(UTC))

class DialogueEntry(SQLModel):
    model_config = {  # noqa: RUF012
        "from_attributes": True,
    }

    speaker: str
    text: str
    start_time: float
    end_time: float


class TemplateMetadata(SQLModel):
    name: TemplateName
    description: str
    category: Literal["common"]
    beta: bool = False
    is_chronological: bool = False





class MinuteVersion(BaseTable, table=True):
    html_content: str
    template: TemplateMetadata = Field(sa_column=Column(JSONB))
    transcription_id: UUID = Field(foreign_key="transcription.id")
    transcription: "Transcription" = Relationship(back_populates="minute_versions")
    trace_id: str | None = Field(default=None)
    star_rating: int | None = Field(default=None)
    star_rating_comment: str | None = Field(default=None)
    is_generating: bool | None = Field(default=False)
    error_message: str | None = Field(default=None)


# Main models with table=True for DB tables
class User(BaseTable, table=True):
    email: str = Field(index=True)
    azure_user_id: str = Field(unique=True, index=True)
    has_completed_onboarding: bool = Field(default=False)
    transcriptions: list["Transcription"] = Relationship(back_populates="user")


class Transcription(BaseTable, table=True):
    user_id: UUID = Field(default=None, foreign_key="user.id")
    user: User | None = Relationship(back_populates="transcriptions")
    title: str | None = Field(default=None)
    minute_versions: list["MinuteVersion"] = Relationship(back_populates="transcription")
    transcription_jobs: list["TranscriptionJob"] = Relationship(back_populates="transcription")


class TranscriptionJob(BaseTable, table=True):
    transcription_id: UUID = Field(foreign_key="transcription.id")
    transcription: "Transcription" = Relationship(back_populates="transcription_jobs")
    dialogue_entries: list[DialogueEntry] = Field(sa_column=Column(JSONB))
    error_message: str | None = Field(default=None)
    s3_audio_url: str | None = Field(default=None)
    # Blob deletion cleanup fields
    needs_cleanup: bool = Field(default=False)
    cleanup_failure_reason: str | None = Field(default=None)


class BlobProcessingAttempt(BaseTable, table=True):
    """
    Track processing attempts for audio blobs to prevent infinite retries.

    This table maintains a record of how many times each blob has been attempted
    for processing, enabling strict retry limit enforcement (max 2 attempts).
    Used by GlobalTranscriptionPollingService to prevent infinite retry loops.

    Attributes
    ----------
    blob_path : str
        Full Azure blob path (unique), indexed for fast lookups
    attempt_count : int
        Number of processing attempts recorded, defaults to 0
    last_error : str | None
        Last error message encountered during processing
    last_attempt_at : datetime
        Timestamp of most recent processing attempt (UTC)
    """

    __tablename__ = "blob_processing_attempt"

    blob_path: str = Field(index=True, unique=True)
    attempt_count: int = Field(default=0)
    last_error: str | None = Field(default=None)
    last_attempt_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# Database helper functions for blob deletion service
async def get_transcription_job_by_id(session: AsyncSession, job_id: UUID) -> TranscriptionJob | None:
    """
    Get a transcription job by its ID.

    Args:
        session: The database session
        job_id: The UUID of the transcription job

    Returns:
        TranscriptionJob | None: The transcription job if found, None otherwise
    """
    stmt = select(TranscriptionJob).where(TranscriptionJob.id == job_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_transcription_jobs_needing_cleanup(session: AsyncSession) -> list[TranscriptionJob]:
    """
    Get all transcription jobs that need manual cleanup.

    Args:
        session: The database session

    Returns:
        list[TranscriptionJob]: List of transcription jobs flagged for manual cleanup
    """
    stmt = select(TranscriptionJob).where(TranscriptionJob.needs_cleanup)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def mark_cleanup_complete(session: AsyncSession, job_id: UUID) -> bool:
    """
    Mark a transcription job as having completed cleanup successfully.

    Args:
        session: The database session
        job_id: The UUID of the transcription job

    Returns:
        bool: True if the job was found and updated, False otherwise
    """
    job = await get_transcription_job_by_id(session, job_id)
    if job:
        job.needs_cleanup = False
        job.cleanup_failure_reason = None
        return True
    return False


async def mark_cleanup_failed(
    session: AsyncSession,
    job_id: UUID,
    error_message: str
) -> bool:
    """
    Mark a transcription job as having failed cleanup and flag for manual intervention.

    Args:
        session: The database session
        job_id: The UUID of the transcription job
        error_message: The error message describing the failure

    Returns:
        bool: True if the job was found and updated, False otherwise
    """
    job = await get_transcription_job_by_id(session, job_id)
    if job:
        job.needs_cleanup = True
        job.cleanup_failure_reason = error_message
        return True
    return False
