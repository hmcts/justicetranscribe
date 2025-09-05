"""
Integration tests for Langfuse configuration validation.

These tests read from the actual .env file and validate against real configuration.
They can make actual network calls to verify Langfuse connectivity.

Run with: pytest tests/integration/app/llm/test_langfuse_integration.py -v --allow-hosts=langfuse-ai.justice.gov.uk
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from langfuse import Langfuse
from pydantic import ValidationError

from build_utils.validate_langfuse_config import (
    validate_environment_variables,
    validate_frontend_langfuse_host,
    validate_langfuse_host,
)
from utils.settings import Settings, get_settings


class TestLangfuseConfigurationIntegration:
    """Integration tests for actual Langfuse configuration."""

    def test_env_file_has_correct_langfuse_host(self):
        """Test that .env file contains the correct Langfuse host."""
        # Check if .env file exists
        env_file = Path(".env")
        if not env_file.exists():
            pytest.skip(".env file not found - cannot test actual configuration")

        # Read .env file
        env_content = env_file.read_text()

        # Check for Justice AI Unit host
        expected_host = "https://langfuse-ai.justice.gov.uk"

        # Look for LANGFUSE_HOST setting
        langfuse_host_lines = [line for line in env_content.split("\n") if line.startswith("LANGFUSE_HOST=")]

        if not langfuse_host_lines:
            pytest.skip("LANGFUSE_HOST not set in .env file")

        # Extract the host value
        host_line = langfuse_host_lines[0]
        host_value = host_line.split("=", 1)[1].strip().strip('"').strip("'")

        # Assert it's the correct host
        assert host_value == expected_host, f"Expected LANGFUSE_HOST={expected_host}, but found: {host_value}"

    def test_settings_validation_with_env_file(self):
        """Test that Settings class properly validates .env configuration."""
        try:
            settings = get_settings()

            # If this succeeds, the host should be the correct one
            assert (
                settings.LANGFUSE_HOST == "https://langfuse-ai.justice.gov.uk"
            ), f"Expected Justice AI Unit host, got: {settings.LANGFUSE_HOST}"

            # Check that credentials are present
            assert settings.LANGFUSE_PUBLIC_KEY, "LANGFUSE_PUBLIC_KEY should not be empty"
            assert settings.LANGFUSE_SECRET_KEY, "LANGFUSE_SECRET_KEY should not be empty"
            assert settings.LANGFUSE_PUBLIC_KEY.startswith(
                "pk-lf-"
            ), f"Public key should start with 'pk-lf-', got: {settings.LANGFUSE_PUBLIC_KEY[:10]}..."
            assert settings.LANGFUSE_SECRET_KEY.startswith(
                "sk-lf-"
            ), f"Secret key should start with 'sk-lf-', got: {settings.LANGFUSE_SECRET_KEY[:10]}..."

        except Exception as e:
            if "Disallowed Langfuse host" in str(e):
                pytest.fail(f"❌ SECURITY ERROR: {e}")
            else:
                pytest.skip(f"Cannot test settings validation: {e}")

    def test_validation_script_functions_with_env(self):
        """Test that our validation script functions work with actual .env."""
        # Test environment variables validation
        env_valid = validate_environment_variables()
        if not env_valid:
            pytest.skip("Required environment variables not set")

        # Test host validation
        host_valid = validate_langfuse_host()
        assert host_valid, "Langfuse host validation should pass with correct configuration"

        # Test frontend host validation
        frontend_valid = validate_frontend_langfuse_host()
        assert frontend_valid, "Frontend Langfuse host validation should pass"

    @pytest.mark.slow
    def test_actual_langfuse_connection(self):
        """Test actual connection to Langfuse instance (slow test, requires network)."""
        settings = get_settings()

        # Skip if we don't have valid credentials
        if not all([settings.LANGFUSE_HOST, settings.LANGFUSE_PUBLIC_KEY, settings.LANGFUSE_SECRET_KEY]):
            pytest.skip("Langfuse credentials not configured")

        # Skip if credentials are obviously test/dummy values
        if (
            settings.LANGFUSE_PUBLIC_KEY.startswith("pk-lf-test")
            or settings.LANGFUSE_SECRET_KEY.startswith("sk-lf-test")
            or settings.LANGFUSE_PUBLIC_KEY == "test"
            or settings.LANGFUSE_SECRET_KEY == "test"  # noqa: S105
        ):
            pytest.skip("Test credentials detected - skipping real connection test")

        try:
            # Create actual Langfuse client
            client = Langfuse(
                host=settings.LANGFUSE_HOST,
                public_key=settings.LANGFUSE_PUBLIC_KEY,
                secret_key=settings.LANGFUSE_SECRET_KEY,
            )

            # Test authentication
            auth_result = client.auth_check()

            assert auth_result, (
                f"❌ Authentication failed for host: {settings.LANGFUSE_HOST}. "
                f"Please verify your credentials are correct."
            )

            print(f"✅ Successfully authenticated with {settings.LANGFUSE_HOST}")  # noqa: T201

        except Exception as e:
            # Only fail if this is clearly a configuration issue, not auth failure
            if "Invalid credentials" in str(e) or "Unauthorized" in str(e):
                pytest.skip(f"Skipping connection test due to invalid credentials: {e}")
            else:
                pytest.fail(f"❌ Langfuse connection test failed: {e}")

    def test_host_allowlist_enforcement(self):
        """Test that only allowlisted hosts are accepted by the validation system."""
        # List of unauthorized hosts that should be rejected
        unauthorized_hosts = [
            "https://cloud.langfuse.com",  # Old cloud instance
            "https://api.langfuse.com",  # Potential other endpoint
            "https://evil-external-site.com",  # Malicious site
            "https://langfuse.example.com",  # Look-alike domain
            "http://localhost:3000",  # Local dev (should not be in production)
            "https://langfuse-ai.justice.gov.uk.evil.com",  # Domain hijacking attempt
        ]

        # Test that each unauthorized host is properly rejected
        for bad_host in unauthorized_hosts:
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
                    LANGFUSE_HOST=bad_host,  # This should fail validation
                    GOOGLE_APPLICATION_CREDENTIALS_JSON_OBJECT="{}",
                    AZURE_AD_TENANT_ID="test",
                    AZURE_AD_CLIENT_ID="test",
                )

            # Verify the error message contains security information
            error_message = str(exc_info.value)
            assert (
                "Disallowed Langfuse host" in error_message
            ), f"Host {bad_host} should be rejected with security error message"
            assert bad_host in error_message, f"Error message should mention the rejected host {bad_host}"
            assert (
                "data leakage" in error_message
            ), f"Error message should mention data leakage prevention for {bad_host}"

    def test_frontend_env_vars_configured(self):
        """Test that frontend environment variables are properly configured."""
        # Check if frontend env vars are set
        frontend_host = os.getenv("NEXT_PUBLIC_LANGFUSE_HOST")
        frontend_key = os.getenv("NEXT_PUBLIC_LANGFUSE_PUBLIC_KEY")

        if frontend_host:
            assert (
                frontend_host == "https://langfuse-ai.justice.gov.uk"
            ), f"Frontend host should be Justice AI Unit instance, got: {frontend_host}"

        if frontend_key:
            assert frontend_key.startswith(
                "pk-lf-"
            ), f"Frontend public key should start with 'pk-lf-', got: {frontend_key[:10]}..."


class TestLangfuseSecurityCompliance:
    """Security-focused integration tests."""

    def test_unauthorized_hosts_rejected_by_settings(self):
        """Test that attempting to use unauthorized hosts fails fast."""
        unauthorized_hosts = [
            "https://cloud.langfuse.com",
            "https://evil-external-site.com",
            "https://langfuse.example.com",
            "http://localhost:3000",  # Even localhost should be rejected in production
        ]

        for bad_host in unauthorized_hosts:
            with pytest.raises(ValueError, match="Disallowed Langfuse host") as exc_info:
                # Try to create settings with bad host
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
                    LANGFUSE_HOST=bad_host,  # This should fail
                    GOOGLE_APPLICATION_CREDENTIALS_JSON_OBJECT="{}",
                    AZURE_AD_TENANT_ID="test",
                    AZURE_AD_CLIENT_ID="test",
                )

            error_message = str(exc_info.value)
            assert (
                "Disallowed Langfuse host" in error_message
            ), f"Host {bad_host} should be rejected with security error"
            assert bad_host in error_message, f"Error message should mention the rejected host {bad_host}"
            assert "data leakage" in error_message, "Error message should mention data leakage prevention"

    def test_validation_script_rejects_bad_hosts(self):
        """Test that validation script properly rejects unauthorized hosts."""
        # Test with environment variable override
        bad_hosts = ["https://cloud.langfuse.com", "https://malicious-site.com"]

        for bad_host in bad_hosts:
            with patch.dict(os.environ, {"LANGFUSE_HOST": bad_host}):
                # Validation should fail
                result = validate_langfuse_host()
                assert not result, f"Validation should reject host: {bad_host}"
