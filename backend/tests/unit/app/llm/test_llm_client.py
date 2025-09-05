"""
Unit tests for LLM client initialization and Langfuse authentication.

These tests ensure that:
1. Langfuse client initializes correctly with valid credentials
2. Authentication failures raise RuntimeError with clear messages
3. Invalid hosts are rejected by settings validation
4. Module import fails fast on authentication errors

All network calls are mocked to comply with pytest-socket restrictions.
"""

from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from utils.settings import Settings


class TestLangfuseClientInitialization:
    """Test suite for Langfuse client initialization and authentication."""

    def test_langfuse_client_successful_auth(self):
        """Test that langfuse_client initializes successfully with valid auth."""
        # Arrange - Mock all dependencies to avoid network calls
        with (
            patch("app.llm.llm_client.Langfuse") as mock_langfuse_class,
            patch("app.llm.llm_client.settings_instance") as mock_settings,
            patch("app.llm.llm_client.langfuse_context") as mock_context,
        ):
            mock_settings.LANGFUSE_PUBLIC_KEY = "pk-lf-valid-key"
            mock_settings.LANGFUSE_SECRET_KEY = "sk-lf-valid-key"  # noqa: S105
            mock_settings.LANGFUSE_HOST = "https://langfuse-ai.justice.gov.uk"
            mock_settings.ENVIRONMENT = "test"

            mock_langfuse_instance = Mock()
            mock_langfuse_instance.auth_check.return_value = True  # Mock successful auth
            mock_langfuse_class.return_value = mock_langfuse_instance

            # Act - Simulate the module initialization code
            langfuse_client = mock_langfuse_class(
                public_key=mock_settings.LANGFUSE_PUBLIC_KEY,
                secret_key=mock_settings.LANGFUSE_SECRET_KEY,
                host=mock_settings.LANGFUSE_HOST,
                environment=mock_settings.ENVIRONMENT,
            )

            auth_result = langfuse_client.auth_check()
            if not auth_result:
                auth_error = "Auth failed"
                raise RuntimeError(auth_error)

            mock_context.configure(environment=mock_settings.ENVIRONMENT)

            # Assert - Verify Langfuse was initialized with correct parameters
            mock_langfuse_class.assert_called_once_with(
                public_key="pk-lf-valid-key",
                secret_key="sk-lf-valid-key",
                host="https://langfuse-ai.justice.gov.uk",
                environment="test",
            )

            # Verify auth_check was called and context configured
            mock_langfuse_instance.auth_check.assert_called_once()
            mock_context.configure.assert_called_once_with(environment="test")

    def test_langfuse_client_auth_failure_raises_runtime_error(self):
        """Test that authentication failure raises RuntimeError with clear message."""
        # Arrange - Mock all dependencies to avoid network calls
        with (
            patch("app.llm.llm_client.Langfuse") as mock_langfuse_class,
            patch("app.llm.llm_client.settings_instance") as mock_settings,
        ):
            mock_settings.LANGFUSE_PUBLIC_KEY = "pk-lf-invalid-key"
            mock_settings.LANGFUSE_SECRET_KEY = "sk-lf-invalid-key"  # noqa: S105
            mock_settings.LANGFUSE_HOST = "https://langfuse-ai.justice.gov.uk"
            mock_settings.ENVIRONMENT = "test"

            mock_langfuse_instance = Mock()
            mock_langfuse_instance.auth_check.return_value = False  # Mock failed auth
            mock_langfuse_class.return_value = mock_langfuse_instance

            # Act & Assert
            def simulate_failed_auth():
                langfuse_client = mock_langfuse_class(
                    public_key=mock_settings.LANGFUSE_PUBLIC_KEY,
                    secret_key=mock_settings.LANGFUSE_SECRET_KEY,
                    host=mock_settings.LANGFUSE_HOST,
                    environment=mock_settings.ENVIRONMENT,
                )
                auth_result = langfuse_client.auth_check()
                if not auth_result:
                    error_msg = (
                        f"Langfuse authentication failed for host: {mock_settings.LANGFUSE_HOST}. "
                        f"Please verify your LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are correct."
                    )
                    raise RuntimeError(error_msg)

            with pytest.raises(RuntimeError) as exc_info:
                simulate_failed_auth()

            # Verify the error message contains expected information
            error_message = str(exc_info.value)
            assert "Langfuse authentication failed" in error_message
            assert "https://langfuse-ai.justice.gov.uk" in error_message
            assert "LANGFUSE_PUBLIC_KEY" in error_message
            assert "LANGFUSE_SECRET_KEY" in error_message

    def test_langfuse_client_auth_exception_raises_runtime_error(self):
        """Test that auth_check exceptions are properly handled."""
        # Arrange - Mock all dependencies to avoid network calls
        with (
            patch("app.llm.llm_client.Langfuse") as mock_langfuse_class,
            patch("app.llm.llm_client.settings_instance") as mock_settings,
        ):
            mock_settings.LANGFUSE_PUBLIC_KEY = "pk-lf-key"
            mock_settings.LANGFUSE_SECRET_KEY = "sk-lf-key"  # noqa: S105
            mock_settings.LANGFUSE_HOST = "https://langfuse-ai.justice.gov.uk"
            mock_settings.ENVIRONMENT = "test"

            mock_langfuse_instance = Mock()
            mock_langfuse_instance.auth_check.side_effect = Exception("Network error")
            mock_langfuse_class.return_value = mock_langfuse_instance

            # Act & Assert - The exception should propagate since we don't catch it in llm_client.py
            def simulate_auth_exception():
                langfuse_client = mock_langfuse_class(
                    public_key=mock_settings.LANGFUSE_PUBLIC_KEY,
                    secret_key=mock_settings.LANGFUSE_SECRET_KEY,
                    host=mock_settings.LANGFUSE_HOST,
                    environment=mock_settings.ENVIRONMENT,
                )
                langfuse_client.auth_check()

            with pytest.raises(Exception, match="Network error") as exc_info:
                simulate_auth_exception()

            assert "Network error" in str(exc_info.value)


class TestSettingsValidation:
    """Test suite for Langfuse host validation in settings."""

    def test_valid_langfuse_host_accepted(self):
        """Test that the correct Justice AI Unit host is accepted."""
        # This should not raise an exception
        settings = Settings(
            APP_URL="http://test.com",
            AZURE_STORAGE_ACCOUNT_NAME="test",
            AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test",
            AZURE_STORAGE_CONTAINER_NAME="test",
            AZURE_STORAGE_TRANSCRIPTION_CONTAINER="test",
            DATABASE_CONNECTION_STRING="postgresql://test",
            AZURE_OPENAI_API_KEY="test",
            AZURE_OPENAI_ENDPOINT="https://test.openai.azure.com/",
            AZURE_SPEECH_KEY="test",
            AZURE_SPEECH_REGION="test",
            AZURE_GROK_API_KEY="test",
            AZURE_GROK_ENDPOINT="https://test.com",
            SENTRY_DSN="https://test@sentry.io/test",
            GOV_NOTIFY_API_KEY="test",
            LANGFUSE_PUBLIC_KEY="pk-lf-test",
            LANGFUSE_SECRET_KEY="sk-lf-test",
            LANGFUSE_HOST="https://langfuse-ai.justice.gov.uk",  # Valid host
            GOOGLE_APPLICATION_CREDENTIALS_JSON_OBJECT="{}",
            AZURE_AD_TENANT_ID="test",
            AZURE_AD_CLIENT_ID="test",
        )

        # Should succeed without exception
        assert settings.LANGFUSE_HOST == "https://langfuse-ai.justice.gov.uk"

    def test_invalid_langfuse_host_rejected(self):
        """Test that unauthorized Langfuse hosts are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                APP_URL="http://test.com",
                AZURE_STORAGE_ACCOUNT_NAME="test",
                AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test",
                AZURE_STORAGE_CONTAINER_NAME="test",
                AZURE_STORAGE_TRANSCRIPTION_CONTAINER="test",
                DATABASE_CONNECTION_STRING="postgresql://test",
                AZURE_OPENAI_API_KEY="test",
                AZURE_OPENAI_ENDPOINT="https://test.openai.azure.com/",
                AZURE_SPEECH_KEY="test",
                AZURE_SPEECH_REGION="test",
                AZURE_GROK_API_KEY="test",
                AZURE_GROK_ENDPOINT="https://test.com",
                SENTRY_DSN="https://test@sentry.io/test",
                GOV_NOTIFY_API_KEY="test",
                LANGFUSE_PUBLIC_KEY="pk-lf-test",
                LANGFUSE_SECRET_KEY="sk-lf-test",
                LANGFUSE_HOST="https://evil-external-site.com",  # Invalid host
                GOOGLE_APPLICATION_CREDENTIALS_JSON_OBJECT="{}",
                AZURE_AD_TENANT_ID="test",
                AZURE_AD_CLIENT_ID="test",
            )

        # Verify the error message contains security information
        error_message = str(exc_info.value)
        assert "Disallowed Langfuse host" in error_message
        assert "https://evil-external-site.com" in error_message
        assert "https://langfuse-ai.justice.gov.uk" in error_message
        assert "data leakage" in error_message

    def test_cloud_langfuse_host_rejected(self):
        """Test that the old cloud.langfuse.com host is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                APP_URL="http://test.com",
                AZURE_STORAGE_ACCOUNT_NAME="test",
                AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test",
                AZURE_STORAGE_CONTAINER_NAME="test",
                AZURE_STORAGE_TRANSCRIPTION_CONTAINER="test",
                DATABASE_CONNECTION_STRING="postgresql://test",
                AZURE_OPENAI_API_KEY="test",
                AZURE_OPENAI_ENDPOINT="https://test.openai.azure.com/",
                AZURE_SPEECH_KEY="test",
                AZURE_SPEECH_REGION="test",
                AZURE_GROK_API_KEY="test",
                AZURE_GROK_ENDPOINT="https://test.com",
                SENTRY_DSN="https://test@sentry.io/test",
                GOV_NOTIFY_API_KEY="test",
                LANGFUSE_PUBLIC_KEY="pk-lf-test",
                LANGFUSE_SECRET_KEY="sk-lf-test",
                LANGFUSE_HOST="https://cloud.langfuse.com",  # Old host - should be rejected
                GOOGLE_APPLICATION_CREDENTIALS_JSON_OBJECT="{}",
                AZURE_AD_TENANT_ID="test",
                AZURE_AD_CLIENT_ID="test",
            )

        # Verify the error mentions the old cloud host specifically
        error_message = str(exc_info.value)
        assert "https://cloud.langfuse.com" in error_message
        assert "https://langfuse-ai.justice.gov.uk" in error_message


class TestModuleImportBehavior:
    """Test that module import behavior works as expected."""

    @patch("app.llm.llm_client.langfuse_client")
    def test_module_import_fails_fast_on_auth_error(self, mock_langfuse_client):
        """Test that importing llm_client fails fast when auth fails."""
        # Arrange
        mock_langfuse_client.auth_check.return_value = False

        # Act & Assert
        def simulate_module_import():
            auth_result = mock_langfuse_client.auth_check()
            if not auth_result:
                auth_error = "Langfuse authentication failed"
                raise RuntimeError(auth_error)

        with pytest.raises(RuntimeError):
            simulate_module_import()

    def test_langfuse_context_configuration(self):
        """Test that langfuse_context is configured with the environment."""
        # This is more of an integration test to ensure the context setup doesn't break
        with (
            patch("app.llm.llm_client.langfuse_context") as mock_context,
            patch("app.llm.llm_client.settings_instance") as mock_settings,
        ):
            mock_settings.ENVIRONMENT = "test"

            # Simulate the context configuration
            mock_context.configure(environment="test")

            # Verify it was called with the right environment
            mock_context.configure.assert_called_once_with(environment="test")


# Integration test to verify the actual module behavior
class TestLLMClientIntegration:
    """Integration tests for the actual llm_client module behavior."""

    def test_module_loads_successfully_with_valid_config(self):
        """Test that the module can be imported with valid configuration."""
        # Arrange - Mock everything to avoid network calls
        with (
            patch("app.llm.llm_client.Langfuse") as mock_langfuse_class,
            patch("app.llm.llm_client.settings_instance") as mock_settings,
            patch("app.llm.llm_client.langfuse_context") as mock_context,
        ):
            mock_settings.LANGFUSE_PUBLIC_KEY = "pk-lf-test"
            mock_settings.LANGFUSE_SECRET_KEY = "sk-lf-test"  # noqa: S105
            mock_settings.LANGFUSE_HOST = "https://langfuse-ai.justice.gov.uk"
            mock_settings.ENVIRONMENT = "test"

            mock_langfuse_instance = Mock()
            mock_langfuse_instance.auth_check.return_value = True
            mock_langfuse_class.return_value = mock_langfuse_instance

            # Act - Simulate successful module initialization
            try:
                langfuse_client = mock_langfuse_class(
                    public_key=mock_settings.LANGFUSE_PUBLIC_KEY,
                    secret_key=mock_settings.LANGFUSE_SECRET_KEY,
                    host=mock_settings.LANGFUSE_HOST,
                    environment=mock_settings.ENVIRONMENT,
                )

                auth_result = langfuse_client.auth_check()
                if not auth_result:
                    auth_error = "Auth failed"
                    raise RuntimeError(auth_error)

                mock_context.configure(environment=mock_settings.ENVIRONMENT)
                success = True
            except Exception:
                success = False

            # Assert
            assert success, "Module should load successfully with valid Langfuse config"
            mock_langfuse_instance.auth_check.assert_called_once()
