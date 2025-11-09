"""
Standalone worker process for the transcription polling service.

This worker runs independently from the API server and continuously polls
Azure Blob Storage for new audio files to process. This separation allows:
- Independent scaling of API and background processing
- Better resource isolation
- Easier monitoring and troubleshooting
"""

import asyncio
import logging

import sentry_sdk

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


async def main():
    """Main entry point for the worker process."""
    log.info("🚀 Starting transcription polling worker...")
    log.info("Environment: %s", settings.ENVIRONMENT)

    try:
        # Create and start the polling service
        polling_service = TranscriptionPollingService()
        await polling_service.run_polling_loop()
    except KeyboardInterrupt:
        log.info("⚠️  Received shutdown signal, stopping worker...")
    except Exception:
        log.exception("❌ Worker error")
        raise
    finally:
        log.info("✅ Worker shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())

