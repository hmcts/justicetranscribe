import logging
from collections.abc import Generator

from dotenv import load_dotenv
from sqlmodel import Session, create_engine, select

from utils.settings import get_settings

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database URL from environment variable
DATABASE_URL = get_settings().DATABASE_CONNECTION_STRING

if not DATABASE_URL:
    msg = "DATABASE_CONNECTION_STRING is not set"
    raise ValueError(msg)

# Create engine with connection pool configuration
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=5,  # Conservative to prevent connection exhaustion
    max_overflow=5,  # Conservative to allow multiple instances
    pool_timeout=30,  # Wait for available connection
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Verify connections before using
)


def get_session() -> Generator[Session, None, None]:
    """Database session dependency"""
    with Session(engine) as session:
        yield session


# def init_db():
#     """Initialize database - create tables"""
#     try:
#         create_db_and_tables()
#         logger.info("Database initialized successfully")
#     except Exception as e:
#         logger.error(f"Error initializing database: {e}")
#         raise


def test_db_connection():
    """Test database connection"""
    try:
        with Session(engine) as session:
            # Simple query to test connection
            session.execute(select(1))
            logger.info("Database connection test successful")
            return True
    except Exception:
        logger.exception("Database connection test failed")
        return False
