import logging

from dotenv import load_dotenv
from sqlmodel import Session, create_engine

from shared_utils.settings import settings_instance

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Get database connection details from environment variables
if settings_instance.ENVIRONMENT == "local":
    logger.info("Loading in dev mode")
    DB_USER = settings_instance.POSTGRES_USER
    DB_PASSWORD = settings_instance.POSTGRES_PASSWORD
    DB_HOST = settings_instance.POSTGRES_HOST
    DB_PORT = settings_instance.POSTGRES_PORT
    DB_NAME = settings_instance.POSTGRES_DB
else:
    DB_USER = settings_instance.POSTGRES_USER
    DB_PASSWORD = settings_instance.POSTGRES_PASSWORD
    DB_HOST = settings_instance.POSTGRES_HOST
    DB_PORT = settings_instance.POSTGRES_PORT
    DB_NAME = settings_instance.POSTGRES_DB

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL)


def get_session():
    with Session(engine) as session:
        yield session
