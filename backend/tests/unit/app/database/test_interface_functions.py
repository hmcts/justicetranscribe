"""Tests for database interface functions."""

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from app.database.interface_functions import save_transcription_job
from app.database.postgres_models import DialogueEntry, TranscriptionJob


@pytest.fixture
def mock_engine():
    """Mock database engine."""
    return MagicMock()


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = MagicMock(spec=Session)
    session.__enter__ = MagicMock(return_value=session)
    session.__exit__ = MagicMock(return_value=False)
    return session


@pytest.mark.unit
def test_save_transcription_job_creates_new_job(mock_session):
    """Test that save_transcription_job can create a new job."""
    # Arrange
    transcription_id = uuid.uuid4()
    job_id = uuid.uuid4()
    job = TranscriptionJob(
        id=job_id,
        transcription_id=str(transcription_id),
        dialogue_entries=[
            DialogueEntry(
                speaker="Speaker 1",
                text="Hello world",
                start_time=0.0,
                end_time=1.0,
            )
        ],
    )

    # Mock the session methods
    mock_session.merge.return_value = job

    # Act
    with patch("app.database.interface_functions.engine") as mock_engine:
        with patch("app.database.interface_functions.Session", return_value=mock_session):
            result = save_transcription_job(job)

    # Assert
    assert result.id == job_id
    mock_session.merge.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(job)


@pytest.mark.unit
def test_save_transcription_job_updates_existing_job(mock_session):
    """Test that save_transcription_job can update an existing job with new speaker names."""
    # Arrange - Create a job that already exists in the database
    transcription_id = uuid.uuid4()
    job_id = uuid.uuid4()
    
    # Original job with old speaker name
    original_job = TranscriptionJob(
        id=job_id,
        transcription_id=str(transcription_id),
        dialogue_entries=[
            DialogueEntry(
                speaker="Speaker 1",
                text="Hello world",
                start_time=0.0,
                end_time=1.0,
            ),
            DialogueEntry(
                speaker="Speaker 1",
                text="How are you?",
                start_time=1.0,
                end_time=2.0,
            )
        ],
        created_datetime=datetime.now(UTC),
    )

    # Updated job with new speaker name (simulating speaker name update)
    updated_job = TranscriptionJob(
        id=job_id,  # Same ID - this is an update
        transcription_id=str(transcription_id),
        dialogue_entries=[
            DialogueEntry(
                speaker="John",  # Updated speaker name
                text="Hello world",
                start_time=0.0,
                end_time=1.0,
            ),
            DialogueEntry(
                speaker="John",  # Updated speaker name
                text="How are you?",
                start_time=1.0,
                end_time=2.0,
            )
        ],
        created_datetime=original_job.created_datetime,
    )

    # Mock the session to return the updated job
    mock_session.merge.return_value = updated_job

    # Act - Save the updated job (this should use merge, not add)
    with patch("app.database.interface_functions.engine") as mock_engine:
        with patch("app.database.interface_functions.Session", return_value=mock_session):
            result = save_transcription_job(updated_job)

    # Assert
    assert result.id == job_id
    assert result.dialogue_entries[0]["speaker"] == "John"
    assert result.dialogue_entries[1]["speaker"] == "John"
    
    # Verify merge was called (not add) - this is critical for updates to work
    mock_session.merge.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(updated_job)


@pytest.mark.unit
def test_save_transcription_job_handles_dialogue_entries_correctly(mock_session):
    """Test that dialogue entries are properly converted before saving."""
    # Arrange
    transcription_id = uuid.uuid4()
    job_id = uuid.uuid4()
    
    # Create job with DialogueEntry objects
    dialogue_entry = DialogueEntry(
        speaker="John",
        text="Test message",
        start_time=0.0,
        end_time=1.0,
    )
    
    job = TranscriptionJob(
        id=job_id,
        transcription_id=str(transcription_id),
        dialogue_entries=[dialogue_entry],
    )

    # Expected job after conversion (dialogue entries as dicts)
    expected_job = TranscriptionJob(
        id=job_id,
        transcription_id=str(transcription_id),
        dialogue_entries=[dialogue_entry.model_dump()],
    )
    
    mock_session.merge.return_value = expected_job

    # Act
    with patch("app.database.interface_functions.engine") as mock_engine:
        with patch("app.database.interface_functions.Session", return_value=mock_session):
            result = save_transcription_job(job)

    # Assert - dialogue entries should be converted to dicts
    mock_session.merge.assert_called_once()
    # Check that the job passed to merge has dialogue_entries as dicts
    call_args = mock_session.merge.call_args
    saved_job = call_args[0][0]
    assert isinstance(saved_job.dialogue_entries[0], dict)
    assert saved_job.dialogue_entries[0]["speaker"] == "John"

