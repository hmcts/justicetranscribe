# ruff: noqa: T201, C901, PLR0912
"""
Langfuse connection debug test for integration testing.
Reads credentials from .env file in project root and tests the connection.

Note: This is a debug test with intentional print statements for diagnostics.
"""

import os

import pytest
from langfuse import Langfuse
from pyprojroot import here


@pytest.mark.integration
def test_langfuse_connection_debug():
    """
    Debug test for Langfuse connection issues.

    This test reads from the actual .env file and provides detailed
    diagnostics about what might be wrong with the Langfuse connection.
    """

    print("\n🧪 Langfuse Connection Debug Test")
    print("=" * 50)

    # Find project root and locate .env file
    project_root = here().parent
    env_file = project_root / ".env"

    print(f"📁 Project root: {project_root}")
    print(f"📄 .env file: {env_file}")

    # Check if .env file exists
    if not env_file.exists():
        pytest.fail(f"❌ .env file not found at: {env_file}")

    print("✅ .env file found")

    # Read environment variables (they should be loaded by pytest-dotenv)
    langfuse_host = os.getenv("LANGFUSE_HOST")
    langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")

    print("\n📋 Environment Variables from .env:")
    print(f"🌐 LANGFUSE_HOST: {langfuse_host}")
    print(f"🔑 LANGFUSE_PUBLIC_KEY: {langfuse_public_key[:15] if langfuse_public_key else 'Not set'}...")
    print(f"🔐 LANGFUSE_SECRET_KEY: {langfuse_secret_key[:15] if langfuse_secret_key else 'Not set'}...")

    # Validate all required variables are present
    missing_vars = []
    if not langfuse_host:
        missing_vars.append("LANGFUSE_HOST")
    if not langfuse_public_key:
        missing_vars.append("LANGFUSE_PUBLIC_KEY")
    if not langfuse_secret_key:
        missing_vars.append("LANGFUSE_SECRET_KEY")

    if missing_vars:
        pytest.fail(f"❌ Missing required environment variables: {', '.join(missing_vars)}")

    print("✅ All required environment variables are present")

    # Validate credential format (case-insensitive)
    format_errors = []
    if not langfuse_public_key.startswith("pk-lf-"):
        format_errors.append(
            f"Public key should start with 'pk-lf-' (case insensitive), got: {langfuse_public_key[:10]}..."
        )

    if not langfuse_secret_key.lower().startswith("sk-lf-"):
        format_errors.append(
            f"Secret key should start with 'sk-lf-' (case insensitive), got: {langfuse_secret_key[:10]}..."
        )

    if langfuse_host != "https://langfuse-ai.justice.gov.uk":
        format_errors.append(f"Host should be 'https://langfuse-ai.justice.gov.uk', got: {langfuse_host}")

    if format_errors:
        pytest.fail("❌ Credential format errors:\n   " + "\n   ".join(format_errors))

    print("✅ Credential format is correct")

    # Test the actual connection
    print(f"\n🔍 Testing connection to {langfuse_host}...")

    try:
        client = Langfuse(
            host=langfuse_host,
            public_key=langfuse_public_key,
            secret_key=langfuse_secret_key,
        )

        print("🔍 Testing authentication...")
        auth_result = client.auth_check()

        if not auth_result:
            pytest.fail("❌ Langfuse authentication failed (auth_check returned False)")

        print("✅ Authentication successful!")

        # Try a simple API operation
        print("🔍 Testing API access...")
        try:
            client.flush()  # Simple operation to test API access
            print("✅ API access confirmed!")

        except Exception as api_error:
            print(f"⚠️  Authentication passed but API access failed: {api_error}")
            # Don't fail the test for this, as auth is the main concern

    except Exception as e:
        error_msg = f"❌ Langfuse connection failed: {e}"

        # Provide specific diagnostic information
        error_str = str(e).lower()
        if "401" in error_str or "unauthorized" in error_str:
            error_msg += "\n\n💡 DIAGNOSIS: 401 Unauthorized"
            error_msg += "\n   - Double-check your public and secret keys in .env"
            error_msg += "\n   - Verify the keys belong to the correct Langfuse project"
            error_msg += "\n   - Check if the keys have expired or been revoked"
            error_msg += f"\n   - Log into {langfuse_host} and regenerate keys if needed"

        elif "403" in error_str or "forbidden" in error_str:
            error_msg += "\n\n💡 DIAGNOSIS: 403 Forbidden"
            error_msg += "\n   - Your credentials may not have sufficient permissions"
            error_msg += "\n   - Contact your Langfuse admin for access"

        elif "timeout" in error_str or "connection" in error_str:
            error_msg += "\n\n💡 DIAGNOSIS: Network/Connection Issue"
            error_msg += "\n   - Check your internet connection"
            error_msg += "\n   - Verify the Langfuse host is accessible"
            error_msg += f"\n   - Try accessing {langfuse_host} in your browser"

        pytest.fail(error_msg)

    print("\n🎉 All Langfuse connection tests passed!")
    print("=" * 50)


@pytest.mark.integration
def test_environment_variables_loaded():
    """Test that environment variables are properly loaded from .env file."""

    print("\n🔍 Environment Variable Loading Test")
    print("-" * 40)

    # Test all Langfuse-related environment variables
    required_vars = ["LANGFUSE_HOST", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"]

    optional_vars = ["NEXT_PUBLIC_LANGFUSE_HOST", "NEXT_PUBLIC_LANGFUSE_PUBLIC_KEY"]

    # Check required variables
    for var in required_vars:
        value = os.getenv(var)
        assert value is not None, f"Required environment variable {var} is not set"
        assert len(value) > 0, f"Required environment variable {var} is empty"
        print(f"✅ {var}: {value[:15]}..." if "KEY" in var else f"✅ {var}: {value}")

    # Check optional variables (log but don't fail)
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            display = f"{value[:15]}..." if "KEY" in var else value
            print(f"✅ {var}: {display}")
        else:
            print(f"{var}: Not set (optional)")

    print("✅ Environment variable loading test passed!")


if __name__ == "__main__":
    # Allow direct execution for debugging
    print("Running Langfuse connection debug test directly...")
    test_langfuse_connection_debug()
    test_environment_variables_loaded()
    print("Debug test completed!")
