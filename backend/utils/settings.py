from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DOCKER_BUILDER_CONTAINER: str

    API_PORT: int = 8080

    APP_URL: str

    APP_NAME: str
    AWS_ACCOUNT_ID: str
    AWS_REGION: str
    ENVIRONMENT: str = "local"

    DATA_S3_BUCKET: str

    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    RUN_MIGRATIONS: bool = False

    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_SPEECH_KEY: str
    AZURE_SPEECH_REGION: str
    BACKEND_HOST: str = "http://localhost:8080"
    SENTRY_DSN: str
    GOV_NOTIFY_API_KEY: str
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_SECRET_KEY: str
    GOOGLE_APPLICATION_CREDENTIALS_JSON_OBJECT: str

    # Uncomment the below to run alembic commands locally, or to run the db interface independently of fastapi
    # from pydantic_settings import SettingsConfigDict
    if ENVIRONMENT == "local":
        model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings():
    return Settings()


settings_instance = get_settings()
