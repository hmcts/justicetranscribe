import os
from sqlmodel import SQLModel, create_engine, Session, select
from typing import Generator
import logging
from dotenv import load_dotenv
from utils.settings import settings_instance

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database URL from environment variable
DATABASE_URL = settings_instance.DATABASE_CONNECTION_STRING

if not DATABASE_URL:
    raise ValueError("DATABASE_CONNECTION_STRING is not set")

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,
)


# def create_db_and_tables():
#     """Create database tables"""
#     logger.info("Creating database tables...")
#     SQLModel.metadata.create_all(engine)
#     logger.info("Database tables created successfully")


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
            result = session.execute(select(1))
            logger.info("Database connection test successful")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False