import uuid
from datetime import datetime
from typing import ClassVar, Literal

from pydantic import BaseModel, Field

from app.database.postgres_models import (
    TemplateMetadata,
)


class TemplateResponse(BaseModel):
    templates: list[TemplateMetadata]


class TranscriptionMetadata(BaseModel):
    """Pydantic model for transcription metadata."""

    id: uuid.UUID
    title: str
    created_datetime: datetime
    updated_datetime: datetime | None = None
    is_showable_in_ui: bool

    class Config:
        json_encoders: ClassVar[dict] = {datetime: lambda dt: dt.isoformat()}


class GenerateMinutesRequest(BaseModel):
    transcription_id: uuid.UUID
    template: TemplateMetadata
    edit_instructions: str | None = None
    current_minute_version_id: uuid.UUID | None = None
    action_type: Literal["generate", "edit"]


class UploadUrlRequest(BaseModel):
    file_extension: str


class SpeakerPrediction(BaseModel):
    original_speaker: str
    predicted_name: str
    confidence: float


class SpeakerPredictionOutput(BaseModel):
    predictions: list[SpeakerPrediction]


class MeetingTitleOutput(BaseModel):
    title: str = Field(description="the title of the meeting")


class UploadUrlResponse(BaseModel):
    upload_url: str
    user_upload_s3_file_key: str
    # transcription_id: uuid.UUID


class StartTranscriptionJobRequest(BaseModel):
    user_upload_s3_file_key: str
    transcription_id: str | None = None


class UpdateUserRequest(BaseModel):
    hide_citations: bool | None = None
    # Add other user fields here as needed
