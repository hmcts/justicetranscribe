"""
Standalone worker process for the transcription polling service.

This worker runs independently from the API server and continuously polls
Azure Blob Storage for new audio files to process. This separation allows:
- Independent scaling of API and background processing
- Better resource isolation
- Easier monitoring and troubleshooting

The worker also includes a minimal HTTP health endpoint to satisfy Azure App Service
startup probes, which expect all applications to respond to HTTP requests.
"""

import asyncio
import logging

import sentry_sdk
import uvicorn
from fastapi import FastAPI
from starlette.responses import JSONResponse

from app.audio.transcription_polling_service import TranscriptionPollingService
from utils.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)

# Initialize settings and Sentry
settings = get_settings()
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,
    send_default_pii=False,
    traces_sample_rate=1.0,
    profile_session_sample_rate=1.0,
    profile_lifecycle="trace",
)

# Create minimal FastAPI app for health checks
health_app = FastAPI(title="Worker Health Service")


@health_app.get("/health")
async def health_check():
    """Health check endpoint for Azure App Service startup probes."""
    return JSONResponse(status_code=200, content={"status": "ok", "service": "worker"})


async def run_health_server():
    """Run the health check HTTP server."""
    log.info("🏥 Starting health check server on port 80...")
    config = uvicorn.Config(
        health_app,
        host="0.0.0.0",
        port=80,
        log_level="warning",  # Reduce uvicorn logs to avoid noise
        access_log=False,     # Disable access logs for health checks
    )
    server = uvicorn.Server(config)
    await server.serve()


async def run_polling_worker():
    """Run the transcription polling service."""
    log.info("⚙️  Starting transcription polling service...")
    polling_service = TranscriptionPollingService()
    await polling_service.run_polling_loop()


async def main():
    """Main entry point for the worker process."""
    log.info("🚀 Starting worker with health endpoint...")
    log.info("Environment: %s", settings.ENVIRONMENT)

    try:
        # Run both the health server and worker concurrently
        # The health server satisfies Azure App Service startup probes
        # The worker handles the actual transcription processing
        await asyncio.gather(
            run_health_server(),
            run_polling_worker()
        )
    except KeyboardInterrupt:
        log.info("⚠️  Received shutdown signal, stopping worker...")
    except Exception:
        log.exception("❌ Worker error")
        raise
    finally:
        log.info("✅ Worker shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())

