import logging
from contextlib import asynccontextmanager

import sentry_sdk
import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer

from api.routes import router as api_router
from utils.cors_utils import parse_origins
from utils.exception_handlers import http_exception_handler, unhandled_exception_handler
from utils.middleware import add_request_id
from utils.settings import get_settings

log = logging.getLogger("uvicorn")


@asynccontextmanager
async def lifespan(app_: FastAPI):  # noqa: ARG001
    log.info("Starting up...")

    yield
    log.info("Shutting down...")


settings = get_settings()
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,
    send_default_pii=False,
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

# Configure CORS based on environment
# For local development, use hardcoded origins
# For deployed environments, use CORS_ALLOWED_ORIGINS from infrastructure
if settings.ENVIRONMENT == "local":
    origins = [
        "http://localhost:3000",  # Local frontend development
        "http://127.0.0.1:3000",  # Alternative localhost
    ]
else:
    origins = parse_origins(settings.CORS_ALLOWED_ORIGINS)

if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,  # Needed for Easy Auth and cookies
        allow_methods=["*"],     # Let OPTIONS succeed without guessing methods
        allow_headers=["*"],     # Avoids 403 on Authorization, custom headers, etc.
        expose_headers=["X-Request-ID"],
        max_age=86400,  # Cache preflight for 24 hours
    )

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Add middleware and exception handlers
@app.middleware("http")
async def request_id_middleware(request, call_next):
    return await add_request_id(request, call_next)

@app.exception_handler(FastAPIHTTPException)
async def http_exception_wrapper(request, exc):  # noqa: ARG001 - request required by FastAPI interface
    return await http_exception_handler(exc)

@app.exception_handler(Exception)
async def unhandled_exception_wrapper(request, exc):  # noqa: ARG001 - request required by FastAPI interface
    return await unhandled_exception_handler(exc)


app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)  # noqa: S104
