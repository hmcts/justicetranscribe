from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    API_PORT: int = 8080

    APP_URL: str

    APP_NAME: str
    AWS_REGION: str
    ENVIRONMENT: str = "local"

    DATA_S3_BUCKET: str
    DATABASE_CONNECTION_STRING: str
    RUN_MIGRATIONS: bool = False

    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_SPEECH_KEY: str
    AZURE_SPEECH_REGION: str
    SENTRY_DSN: str
    GOV_NOTIFY_API_KEY: str
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_SECRET_KEY: str
    GOOGLE_APPLICATION_CREDENTIALS_JSON_OBJECT: str
    LANGFUSE_HOST: str

    # Uncomment the below to run alembic commands locally, or to run the db interface independently of fastapi
    # from pydantic_settings import SettingsConfigDict
    if ENVIRONMENT == "local":
        model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings():
    return Settings()


settings_instance = get_settings()
