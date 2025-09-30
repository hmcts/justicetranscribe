"""Unit tests for environment-specific allowlist configuration."""


import pytest

from utils.settings import Settings


class TestAllowlistEnvironmentConfiguration:
    """Test environment-specific allowlist configuration."""

    @pytest.fixture
    def base_settings(self) -> dict:
        """Base settings fixture to avoid duplication."""
        return {
            "ALLOWLIST_CONTAINER": "application-data",
            "ALLOWLIST_BLOB_NAME": "lookups/allowlist.csv",
            "APP_URL": "http://localhost:3000",
            "AZURE_AD_CLIENT_ID": "dummy",
            "AZURE_AD_TENANT_ID": "dummy",
            "AZURE_GROK_API_KEY": "dummy",
            "AZURE_GROK_ENDPOINT": "dummy",
            "AZURE_OPENAI_API_KEY": "dummy",
            "AZURE_OPENAI_ENDPOINT": "dummy",
            "AZURE_SPEECH_KEY": "dummy",
            "AZURE_SPEECH_REGION": "dummy",
            "AZURE_STORAGE_ACCOUNT_NAME": "dummy",
            "AZURE_STORAGE_CONNECTION_STRING": "dummy",
            "AZURE_STORAGE_CONTAINER_NAME": "dummy",
            "AZURE_STORAGE_TRANSCRIPTION_CONTAINER": "dummy",
            "DATABASE_CONNECTION_STRING": "dummy",
            "GOOGLE_APPLICATION_CREDENTIALS_JSON_OBJECT": "dummy",
            "GOV_NOTIFY_API_KEY": "dummy",
            "LANGFUSE_PUBLIC_KEY": "dummy",
            "LANGFUSE_SECRET_KEY": "dummy",
            "LANGFUSE_HOST": "https://langfuse-ai.justice.gov.uk",  # Mock URL
            "SENTRY_DSN": "dummy",
        }

    def test_get_allowlist_config_local_environment(self, base_settings: dict):
        """Test allowlist config for local environment."""
        settings = Settings(
            ENVIRONMENT="local",
            **base_settings
        )

        config = settings.get_allowlist_config()

        assert config["container"] == "application-data", f"Expected container to be 'application-data', got {config['container']}"
        assert config["blob_name"] == "lookups/allowlist.csv", f"Expected blob_name to be 'lookups/allowlist.csv' for local environment, got {config['blob_name']}"

    def test_get_allowlist_config_dev_environment(self, base_settings: dict):
        """Test allowlist config for dev environment."""
        settings = Settings(
            ENVIRONMENT="dev",
            **base_settings
        )

        config = settings.get_allowlist_config()

        assert config["container"] == "application-data", f"Expected container to be 'application-data', got {config['container']}"
        assert config["blob_name"] == "lookups/allowlist.csv", f"Expected blob_name to be 'lookups/allowlist.csv' for dev environment, got {config['blob_name']}"

    def test_get_allowlist_config_prod_environment(self, base_settings: dict):
        """Test allowlist config for prod environment."""
        settings = Settings(
            ENVIRONMENT="prod",
            **base_settings
        )

        config = settings.get_allowlist_config()

        assert config["container"] == "application-data", f"Expected container to be 'application-data', got {config['container']}"
        assert config["blob_name"] == "lookups/allowlist.csv", f"Expected blob_name to be 'lookups/allowlist.csv' for prod environment, got {config['blob_name']}"

    def test_get_allowlist_config_override_environment(self, base_settings: dict):
        """Test allowlist config with explicit environment override."""
        settings = Settings(
            ALLOWLIST_ENVIRONMENT="prod",  # Override
            ENVIRONMENT="dev",  # This should be ignored
            **base_settings
        )

        config = settings.get_allowlist_config()

        assert config["container"] == "application-data", f"Expected container to be 'application-data', got {config['container']}"
        assert config["blob_name"] == "lookups/allowlist.csv", f"Expected blob_name to be 'lookups/allowlist.csv' for override to prod, got {config['blob_name']}"

    def test_get_allowlist_config_unknown_environment_defaults_to_dev(self, base_settings: dict):
        """Test allowlist config for unknown environment defaults to dev."""
        settings = Settings(
            ENVIRONMENT="unknown",
            **base_settings
        )

        config = settings.get_allowlist_config()

        assert config["container"] == "application-data", f"Expected container to be 'application-data', got {config['container']}"
        assert config["blob_name"] == "lookups/allowlist.csv", f"Expected blob_name to default to 'lookups/allowlist.csv' for unknown environment, got {config['blob_name']}"

    def test_environment_specific_allowlist_paths(self, base_settings: dict):
        """Test that different environments use correct allowlist paths.

        Note: Currently all environments use the same allowlist file.
        This can be changed by uploading separate files for dev/prod if needed.
        """
        test_cases = [
            ("local", "lookups/allowlist.csv"),
            ("dev", "lookups/allowlist.csv"),
            ("prod", "lookups/allowlist.csv"),
            ("unknown", "lookups/allowlist.csv"),
        ]

        for env, expected_blob in test_cases:
            settings = Settings(
                ENVIRONMENT=env,
                **base_settings
            )

            config = settings.get_allowlist_config()
            assert config["blob_name"] == expected_blob, f"Environment {env} should use {expected_blob}, got {config['blob_name']}"
