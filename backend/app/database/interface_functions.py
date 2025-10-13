from datetime import UTC, datetime
from uuid import UUID

import pytz
import sentry_sdk
from fastapi import HTTPException
from sqlalchemy import event
from sqlmodel import Session, select

from app.database.postgres_database import engine
from app.database.postgres_models import (
    BaseTable,
    DialogueEntry,
    MinuteVersion,
    Transcription,
    TranscriptionJob,
    User,
)
from app.minutes.types import TranscriptionMetadata


@event.listens_for(Session, "before_flush")
def before_flush(session, flush_context, instances):  # noqa: ARG001
    for obj in session.dirty:
        if isinstance(obj, BaseTable):
            obj.updated_datetime = datetime.now(UTC)


def save_transcription(
    transcription_data: Transcription,
    user_id: UUID,
) -> Transcription:
    with Session(engine) as session:
        transcription_data.user_id = user_id
        merged = session.merge(transcription_data)
        session.commit()
        session.refresh(merged)
        return merged


def save_minute_version(
    minute_data: MinuteVersion,
) -> MinuteVersion:
    with Session(engine) as session:
        minute_data.template = (
            minute_data.template.model_dump()
            if hasattr(minute_data.template, "model_dump")
            else minute_data.template
        )
        merged = session.merge(minute_data)
        session.commit()
        session.refresh(merged)
        return merged


def _is_transcription_showable(
    transcription: Transcription, current_time: datetime
) -> bool:
    try:
        # Has any minute versions with content or errors
        if transcription.minute_versions and any(
            version.html_content or version.error_message is not None
            for version in transcription.minute_versions
        ):
            return True

        # Any jobs have error messages
        if transcription.transcription_jobs and any(
            job.error_message is not None for job in transcription.transcription_jobs
        ):
            return True

        # Created more than 5 minutes ago
        if transcription.created_datetime:
            created_dt = (
                pytz.utc.localize(transcription.created_datetime)
                if transcription.created_datetime.tzinfo is None
                else transcription.created_datetime
            )
            five_minutes_in_seconds = 300
            if (current_time - created_dt).total_seconds() > five_minutes_in_seconds:
                return True

        return False  # noqa: TRY300
    except Exception as e:
        # If anything goes wrong, default to showing the transcription
        sentry_sdk.capture_exception(e)
        return True


def _extract_unique_speakers(transcription: Transcription) -> list[str]:
    """Extract unique speaker names from all transcription jobs."""
    speakers: set[str] = set()

    for job in transcription.transcription_jobs or []:
        for entry in job.dialogue_entries:
            if isinstance(entry, dict):
                speaker_name = entry.get("speaker", "").strip()
            else:
                speaker_name = getattr(entry, "speaker", "").strip()

            if speaker_name:
                speakers.add(speaker_name.title())

    return sorted(speakers)


def fetch_transcriptions_metadata(user_id: UUID, tz) -> list[TranscriptionMetadata]:
    with Session(engine) as session:
        statement = select(Transcription).where(Transcription.user_id == user_id)
        transcriptions = session.exec(statement).all()

        current_time = datetime.now(UTC)

        return [
            TranscriptionMetadata(
                id=t.id,
                title=t.title or "",
                created_datetime=pytz.utc.localize(t.created_datetime).astimezone(tz),
                updated_datetime=(
                    pytz.utc.localize(t.updated_datetime).astimezone(tz)
                    if t.updated_datetime
                    else None
                ),
                is_showable_in_ui=_is_transcription_showable(t, current_time),
                speakers=_extract_unique_speakers(t),
            )
            for t in transcriptions
        ]


def get_transcription_by_id(transcription_id: UUID, user_id: UUID, tz) -> Transcription:
    with Session(engine) as session:
        statement = select(Transcription).where(
            Transcription.id == transcription_id,
            Transcription.user_id == user_id,
        )
        transcription = session.exec(statement).first()
        if not transcription:
            raise HTTPException(status_code=404, detail="Transcription not found")

        # Convert the date to local timezone
        if transcription.created_datetime:
            transcription.created_datetime = pytz.utc.localize(
                transcription.created_datetime
            ).astimezone(tz)
        if transcription.updated_datetime:
            transcription.updated_datetime = pytz.utc.localize(
                transcription.updated_datetime
            ).astimezone(tz)

        return transcription


def delete_transcription_by_id(
    transcription_id: UUID,
    user_id: UUID,
) -> None:
    with Session(engine) as session:
        statement = select(Transcription).where(
            Transcription.id == transcription_id,
            Transcription.user_id == user_id,
        )
        transcription = session.exec(statement).first()

        if not transcription:
            raise HTTPException(status_code=404, detail="Transcription not found")

        minute_versions = get_minute_versions(transcription_id)
        for version in minute_versions:
            session.delete(version)

        transcription_jobs = get_transcription_jobs(transcription_id)
        for job in transcription_jobs:
            session.delete(job)

        session.delete(transcription)
        session.commit()


def get_minute_versions(
    transcription_id: UUID,
) -> list[MinuteVersion]:
    with Session(engine) as session:
        # First verify the transcription exists
        transcription = session.get(Transcription, transcription_id)
        if not transcription:
            raise HTTPException(status_code=404, detail="Transcription not found")

        statement = select(MinuteVersion).where(
            MinuteVersion.transcription_id == transcription_id
        )
        results = session.exec(statement).all()
        return list(results)


def get_minute_version_by_id(
    minute_version_id: UUID,
    transcription_id: UUID,
) -> MinuteVersion:
    minute_versions = get_minute_versions(transcription_id)
    for version in minute_versions:
        if UUID(str(version.id)) == UUID(str(minute_version_id)):
            return version
    raise HTTPException(status_code=404, detail="Minute version not found")


def save_transcription_job(
    job: TranscriptionJob,
) -> TranscriptionJob:
    with Session(engine) as session:
        job.dialogue_entries = [
            entry.model_dump() if hasattr(entry, "model_dump") else entry
            for entry in job.dialogue_entries
        ]
        merged = session.merge(job)
        session.commit()
        session.refresh(merged)
        return merged


def get_transcription_jobs(
    transcription_id: UUID,
) -> list[TranscriptionJob]:
    with Session(engine) as session:
        transcription = session.get(Transcription, transcription_id)
        if not transcription:
            raise HTTPException(status_code=404, detail="Transcription not found")

        statement = select(TranscriptionJob).where(
            TranscriptionJob.transcription_id == transcription_id
        )
        results = session.exec(statement).all()

        for job in results:
            job.dialogue_entries = [
                DialogueEntry(**entry) for entry in job.dialogue_entries
            ]

        return list(results)


def get_user_by_id(user_id: UUID) -> User:
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user


def update_user(user_id: UUID, **kwargs) -> User:
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def mark_user_onboarding_complete(user_id: UUID) -> User:
    """Mark user as having completed onboarding"""
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.has_completed_onboarding = True
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
