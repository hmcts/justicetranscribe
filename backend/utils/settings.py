from functools import lru_cache

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

    # JWT Verification Settings - Strict by default
    AZURE_AD_TENANT_ID: str
    AZURE_AD_CLIENT_ID: str
    ENABLE_JWT_VERIFICATION: bool = True
    JWT_VERIFICATION_STRICT: bool = True

    # Onboarding Override for Development Testing
    FORCE_ONBOARDING_DEV: bool = False

    # Uncomment the below to run alembic commands locally, or to run the db interface independently of fastapi
    # from pydantic_settings import SettingsConfigDict
    if ENVIRONMENT == "local":
        model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings():
    return Settings()


settings_instance = get_settings()
