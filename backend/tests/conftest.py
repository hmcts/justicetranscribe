"""Pytest configuration and shared fixtures."""

import asyncio
import os
from typing import Any, AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Add the backend directory to Python path for imports
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


def pytest_addoption(parser):
    """Add command line option to run integration tests."""
    parser.addoption(
        "--integration", 
        action="store_true", 
        default=False,
        help="Run integration tests (skipped by default)"
    )


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings() -> MagicMock:
    """Mock application settings."""
    settings = MagicMock()
    settings.DATABASE_URL = "postgresql://test:test@localhost:5432/test_db"
    settings.AZURE_STORAGE_CONNECTION_STRING = "test_connection_string"
    settings.AZURE_CONTAINER_NAME = "test-container"
    settings.OPENAI_API_KEY = "test-openai-key"
    settings.ENVIRONMENT = "test"
    return settings


@pytest.fixture
def mock_database():
    """Mock database session."""
    return MagicMock()


@pytest.fixture
def mock_azure_client() -> MagicMock:
    """Mock Azure Blob Service Client."""
    mock_client = MagicMock()
    mock_blob_client = MagicMock()
    mock_client.get_blob_client.return_value = mock_blob_client
    mock_blob_client.upload_blob.return_value = None
    mock_blob_client.download_blob.return_value.readall.return_value = b"test audio data"
    return mock_client


@pytest.fixture
def mock_openai_client() -> AsyncMock:
    """Mock OpenAI client for testing LLM interactions."""
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test AI response"
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    return mock_client


@pytest.fixture
def sample_audio_file(tmp_path: Path) -> Path:
    """Create a sample audio file for testing."""
    audio_file = tmp_path / "test_audio.wav"
    # Create a minimal WAV file header
    wav_header = (
        b"RIFF"
        + (44 - 8).to_bytes(4, "little")
        + b"WAVE"
        + b"fmt "
        + (16).to_bytes(4, "little")
        + (1).to_bytes(2, "little")  # PCM format
        + (1).to_bytes(2, "little")  # mono
        + (44100).to_bytes(4, "little")  # sample rate
        + (88200).to_bytes(4, "little")  # byte rate
        + (2).to_bytes(2, "little")  # block align
        + (16).to_bytes(2, "little")  # bits per sample
        + b"data"
        + (0).to_bytes(4, "little")  # data size
    )
    audio_file.write_bytes(wav_header)
    return audio_file


@pytest.fixture
def sample_transcript() -> dict[str, Any]:
    """Sample transcript data for testing."""
    return {
        "text": "This is a test transcript with multiple speakers discussing important topics.",
        "speakers": [
            {
                "id": "speaker_1",
                "name": "John Doe",
                "segments": [
                    {"start": 0.0, "end": 5.0, "text": "This is a test transcript"},
                ],
            },
            {
                "id": "speaker_2", 
                "name": "Jane Smith",
                "segments": [
                    {"start": 5.0, "end": 10.0, "text": "with multiple speakers discussing"},
                ],
            },
        ],
        "duration": 10.0,
    }


@pytest.fixture
def sample_meeting_data() -> dict[str, Any]:
    """Sample meeting data for testing."""
    return {
        "title": "Test Meeting",
        "agenda": "Discuss test procedures and implementation",
        "participants": ["John Doe", "Jane Smith", "Bob Johnson"],
        "date": "2024-01-15",
        "duration": 3600,  # 1 hour in seconds
    }


@pytest.fixture
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client for API testing."""
    # Import here to avoid circular imports
    from main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sync_test_client() -> TestClient:
    """Create synchronous test client for API testing."""
    from main import app
    
    return TestClient(app)


# Environment setup for tests
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up test environment variables."""
    test_env_vars = {
        "ENVIRONMENT": "test",
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test_db",
        "AZURE_STORAGE_CONNECTION_STRING": "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test;EndpointSuffix=core.windows.net",
        "AZURE_CONTAINER_NAME": "test-container",
        "OPENAI_API_KEY": "test-key",
        "JWT_SECRET_KEY": "test-jwt-secret",
        "SENTRY_DSN": "",  # Disable Sentry in tests
    }
    
    for key, value in test_env_vars.items():
        monkeypatch.setenv(key, value)


# Pytest configuration
def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "azure: mark test as requiring Azure services"
    )
    config.addinivalue_line(
        "markers", "database: mark test as requiring database"
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Automatically mark tests based on their location and skip integration tests by default."""
    # Skip integration tests by default unless --integration flag is used
    skip_integration = not config.getoption("--integration")
    
    for item in items:
        # Get the test file path relative to tests directory
        test_path = Path(item.fspath).relative_to(Path(__file__).parent)
        
        # Auto-mark based on directory structure
        if test_path.parts[0] == "unit":
            item.add_marker(pytest.mark.unit)
        elif test_path.parts[0] == "integration":
            item.add_marker(pytest.mark.integration)
            # Skip integration tests by default
            if skip_integration:
                item.add_marker(pytest.mark.skip(reason="Integration test skipped. Use --integration to run."))
        elif test_path.parts[0] == "e2e":
            item.add_marker(pytest.mark.e2e)
