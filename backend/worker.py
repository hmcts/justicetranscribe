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
from app.database.postgres_database import engine
from utils.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)

# Initialize settings and Sentry
settings = get_settings()
log.info("🔧 Settings initialized")

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,
    send_default_pii=False,
    traces_sample_rate=1.0,
    profile_session_sample_rate=1.0,
    profile_lifecycle="trace",
)
log.info("📊 Sentry initialized")

# Create minimal FastAPI app for health checks
health_app = FastAPI(title="Worker Health Service")


async def test_startup_connectivity():
    """Test connectivity to critical services during startup."""
    log.info("🔍 Testing startup connectivity...")
    
    try:
        # Test database connection
        log.info("🔍 Testing database connection...")
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        log.info("✅ Database connection successful")
        
        # Test Azure Storage connection  
        log.info("🔍 Testing Azure Storage connection...")
        from app.audio.azure_utils import AsyncAzureBlobManager
        AsyncAzureBlobManager()  # Just test instantiation
        log.info("✅ Azure Storage manager created successfully")
        
    except Exception as e:
        log.exception("❌ Startup connectivity test failed: %s", e)
        raise


@health_app.get("/health")
async def health_check():
    """Health check endpoint for Azure App Service startup probes."""
    return JSONResponse(status_code=200, content={"status": "ok", "service": "worker"})


async def run_health_server():
    """Run the health check HTTP server."""
    log.info("🏥 Starting health check server on port 80...")
    try:
        config = uvicorn.Config(
            health_app,
            host="0.0.0.0",
            port=80,
            log_level="warning",  # Reduce uvicorn logs to avoid noise
            access_log=False,     # Disable access logs for health checks
        )
        server = uvicorn.Server(config)
        log.info("🏥 Health server config created, starting server...")
        await server.serve()
    except Exception as e:
        log.exception("❌ Health server failed to start: %s", e)
        raise


async def run_polling_worker():
    """Run the transcription polling service."""
    log.info("⚙️  Starting transcription polling service...")
    try:
        log.info("⚙️  Creating TranscriptionPollingService instance...")
        polling_service = TranscriptionPollingService()
        log.info("⚙️  TranscriptionPollingService created successfully")
        log.info("⚙️  Starting polling loop...")
        await polling_service.run_polling_loop()
    except Exception as e:
        log.exception("❌ Polling service failed: %s", e)
        raise


async def main():
    """Main entry point for the worker process."""
    log.info("🚀 Starting worker with health endpoint...")
    log.info("Environment: %s", settings.ENVIRONMENT)
    log.info("🔧 Settings loaded successfully")

    try:
        # Test connectivity to critical services before starting main tasks
        await test_startup_connectivity()
        
        log.info("🏃 Creating concurrent tasks for health server and polling service...")
        
        # Run both the health server and worker concurrently
        # The health server satisfies Azure App Service startup probes  
        # The worker handles the actual transcription processing
        health_task = asyncio.create_task(run_health_server(), name="health-server")
        worker_task = asyncio.create_task(run_polling_worker(), name="polling-worker")
        
        log.info("🏃 Tasks created, starting concurrent execution...")
        await asyncio.gather(health_task, worker_task)
        
    except KeyboardInterrupt:
        log.info("⚠️  Received shutdown signal, stopping worker...")
    except Exception as e:
        log.exception("❌ Worker error: %s", e)
        raise
    finally:
        log.info("✅ Worker shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())

