import os
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_PORT: int = 8080

    APP_URL: str

    ENVIRONMENT: str = "local"

    # Azure Storage Configuration (replacing AWS S3)
    AZURE_STORAGE_ACCOUNT_NAME: str
    AZURE_STORAGE_CONNECTION_STRING: str
    AZURE_STORAGE_CONTAINER_NAME: str
    AZURE_STORAGE_TRANSCRIPTION_CONTAINER: str
    DATABASE_CONNECTION_STRING: str
    RUN_MIGRATIONS: bool = False

    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_SPEECH_KEY: str
    AZURE_SPEECH_REGION: str
    AZURE_GROK_API_KEY: str
    AZURE_GROK_ENDPOINT: str
    SENTRY_DSN: str
    GOV_NOTIFY_API_KEY: str
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_SECRET_KEY: str
    GOOGLE_APPLICATION_CREDENTIALS_JSON_OBJECT: str
    LANGFUSE_HOST: str

    @field_validator("LANGFUSE_HOST")
    @classmethod
    def validate_langfuse_host(cls, v):
        """Validate that only the approved Justice AI Unit Langfuse instance is used."""
        allowed_host = "https://langfuse-ai.justice.gov.uk"
        if v != allowed_host:
            error_msg = (
                f"Disallowed Langfuse host '{v}'. Only {allowed_host} is permitted. "
                f"This prevents accidental data leakage to unauthorized instances."
            )
            raise ValueError(error_msg)
        return v

    # JWT Verification Settings - Strict by default
    AZURE_AD_TENANT_ID: str
    AZURE_AD_CLIENT_ID: str
    ENABLE_JWT_VERIFICATION: bool = True
    JWT_VERIFICATION_STRICT: bool = True

    # Load from .env file for local development only
    if os.getenv("ENVIRONMENT") == "local":
        model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings():
    return Settings()


settings_instance = get_settings()
