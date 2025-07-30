from datetime import UTC, datetime
from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
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
