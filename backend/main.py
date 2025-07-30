import logging
from contextlib import asynccontextmanager

import sentry_sdk
import uvicorn
from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer

from api.routes import router as api_router
from utils.settings import settings_instance

log = logging.getLogger("uvicorn")


@asynccontextmanager
async def lifespan(app_: FastAPI):  # noqa: ARG001
    log.info("Starting up...")

    yield
    log.info("Shutting down...")


sentry_sdk.init(
    dsn=settings_instance.SENTRY_DSN,
    environment=settings_instance.ENVIRONMENT,
    send_default_pii=True,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    # Set profile_session_sample_rate to 1.0 to profile 100%
    # of profile sessions.
    profile_session_sample_rate=1.0,
    # Set profile_lifecycle to "trace" to automatically
    # run the profiler on when there is an active transaction
    profile_lifecycle="trace",
)

app = FastAPI(lifespan=lifespan, openapi_url="/api/openapi.json")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)  # noqa: S104
