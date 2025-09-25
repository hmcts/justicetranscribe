import logging
from contextlib import asynccontextmanager
import uuid
import contextvars

import sentry_sdk
import uvicorn
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer

from api.routes import router as api_router
from utils.settings import get_settings

log = logging.getLogger("uvicorn")
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")


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

# Configure CORS for local development only
# Note: In production (Azure App Service), CORS is handled at the infrastructure level
# through Azure's CORS configuration, so we don't need this middleware there
if settings.ENVIRONMENT == "local":
    origins = [
        "http://localhost:3000",  # Local frontend development
        "http://127.0.0.1:3000",  # Alternative localhost
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
        allow_headers=["*"],  # Allow all headers
    )

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    rid = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    request_id_ctx.set(rid)
    response = await call_next(request)
    response.headers["X-Request-Id"] = rid
    return response


@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
    rid = request_id_ctx.get()
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "request_id": rid},
        headers={"X-Request-Id": rid},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    rid = request_id_ctx.get()
    sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "request_id": rid},
        headers={"X-Request-Id": rid},
    )


app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)  # noqa: S104
