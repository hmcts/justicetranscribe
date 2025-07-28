import os
from sqlmodel import SQLModel, create_engine, Session, select
from typing import Generator
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_CONNECTION_STRING")

if not DATABASE_URL:
    # Fallback for local development
    DATABASE_URL = "postgresql://localhost:5432/justicetranscribe_db"
    logger.warning("DATABASE_CONNECTION_STRING not found, using local development URL")

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=True if os.getenv("ENVIRONMENT", "local").lower() in ["local", "development", "dev"] else False,
)


def get_session() -> Generator[Session, None, None]:
    """Database session dependency"""
    with Session(engine) as session:
        yield session




def test_db_connection():
    """Test database connection"""
    try:
        with Session(engine) as session:
            # Simple query to test connection
            result = session.execute(select(1))
            logger.info("Database connection test successful")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False