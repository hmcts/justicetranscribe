import os
from functools import cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_PORT: int = 8080
    APP_URL: str
    AZURE_AD_CLIENT_ID: str
    AZURE_AD_TENANT_ID: str
    AZURE_GROK_API_KEY: str
    AZURE_GROK_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_SPEECH_KEY: str
    AZURE_SPEECH_REGION: str
    # Azure Storage Configuration (replacing AWS S3)
    AZURE_STORAGE_ACCOUNT_NAME: str
    AZURE_STORAGE_CONNECTION_STRING: str
    AZURE_STORAGE_CONTAINER_NAME: str
    AZURE_STORAGE_TRANSCRIPTION_CONTAINER: str
    DATABASE_CONNECTION_STRING: str
    ENVIRONMENT: str = "local"
    GOOGLE_APPLICATION_CREDENTIALS_JSON_OBJECT: str
    GOV_NOTIFY_API_KEY: str
    # JWT Verification Settings - Strict by default
    JWT_ENABLE_VERIFICATION: bool = True
    JWT_VERIFICATION_STRICT: bool = True
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_SECRET_KEY: str
    LANGFUSE_HOST: str
    RUN_MIGRATIONS: bool = False
    SENTRY_DSN: str


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


class LocalSettings(Settings):
    """Settings class that loads from .env file for local development."""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class ProductionSettings(Settings):
    """Settings class for production environments (no .env file)."""
    model_config = SettingsConfigDict(extra="ignore")


@cache
def get_settings(environment: str | None = None):
    """Get Settings instance with optional environment override.

    Args:
        environment: Override environment setting. If None, uses ENVIRONMENT env var or default.

    Returns:
        Settings: Configured settings instance.
    """
    # Handle None case for lru_cache compatibility
    env_key = environment if environment is not None else os.getenv("ENVIRONMENT", "local")

    # Choose the appropriate settings class based on environment
    if env_key == "local":
        return LocalSettings()
    else:
        return ProductionSettings(ENVIRONMENT=env_key)
