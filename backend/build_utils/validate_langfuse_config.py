#!/usr/bin/env python3
# ruff: noqa: T201
"""
Langfuse Configuration Validation Script

This script validates Langfuse configuration during Docker build time
to prevent accidental data leakage to unauthorized instances.

Following the same pattern as validate_azure_config.py to ensure consistency.
"""

import os
import sys
from pathlib import Path

# Add the project root to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from langfuse import Langfuse

# The only allowed Langfuse host for Justice AI Unit
ALLOWED_LANGFUSE_HOST = "https://langfuse-ai.justice.gov.uk"


def is_ci_environment():
    """Check if we're running in a CI/CD environment."""
    ci_indicators = ["CI", "CONTINUOUS_INTEGRATION", "GITHUB_ACTIONS", "AZURE_DEVOPS", "TF_BUILD", "BUILD_BUILDID"]
    return any(os.getenv(indicator) for indicator in ci_indicators)


def validate_environment_variables():
    """Validate that required Langfuse environment variables are present."""
    required_vars = ["LANGFUSE_SECRET_KEY", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_HOST"]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("❌ LANGFUSE CONFIGURATION ERROR: Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 SOLUTION: Ensure these environment variables are set in your:")
        print("   - .env file (for local development)")
        print("   - Docker environment configuration")
        print("   - Terraform/infrastructure configuration")
        return False

    return True


def validate_langfuse_host():
    """Validate that the Langfuse host is the approved Justice AI Unit instance."""
    langfuse_host = os.getenv("LANGFUSE_HOST", "")

    if not langfuse_host:
        print("❌ LANGFUSE CONFIGURATION ERROR: LANGFUSE_HOST is empty")
        return False

    if langfuse_host != ALLOWED_LANGFUSE_HOST:
        print("❌ LANGFUSE SECURITY ERROR: Unauthorized Langfuse host detected")
        print(f"   Configured host: {langfuse_host}")
        print(f"   Allowed host: {ALLOWED_LANGFUSE_HOST}")
        print("\n🛡️ SECURITY PROTECTION:")
        print("   This prevents accidental data leakage to unauthorized Langfuse instances.")
        print("   Only the Justice AI Unit self-hosted instance is permitted.")
        print("\n💡 SOLUTION:")
        print(f"   Set LANGFUSE_HOST={ALLOWED_LANGFUSE_HOST}")
        return False

    print(f"✅ Langfuse host validation passed: {langfuse_host}")
    return True


def validate_langfuse_connection():
    """Validate that we can connect to and authenticate with the Langfuse instance."""
    langfuse_host = os.getenv("LANGFUSE_HOST", "")
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")

    try:
        print("🔍 Validating Langfuse connection and authentication...")

        client = Langfuse(
            host=langfuse_host,
            public_key=public_key,
            secret_key=secret_key,
        )

        auth_result = client.auth_check()

        if auth_result:
            print("✅ Langfuse authentication successful")
            return True
        else:
            print("❌ LANGFUSE AUTHENTICATION FAILED:")
            print("   Authentication check returned False")
            print("\n💡 POSSIBLE SOLUTIONS:")
            print("   - Verify your LANGFUSE_PUBLIC_KEY is correct")
            print("   - Verify your LANGFUSE_SECRET_KEY is correct")
            print(f"   - Ensure the Langfuse instance at {langfuse_host} is accessible")
            print("   - Check if the credentials have the necessary permissions")
            return False

    except Exception as e:
        print("❌ LANGFUSE CONNECTION ERROR:")
        print(f"   Error: {e}")

        # Provide specific guidance based on the error
        error_msg = str(e).lower()
        if "unauthorized" in error_msg or "401" in error_msg:
            print("\n💡 AUTHENTICATION ISSUE:")
            print("   - Check that your public and secret keys are correct")
            print("   - Verify the keys belong to the correct Langfuse project")
        elif "host" in error_msg or "connection" in error_msg:
            print("\n💡 CONNECTION ISSUE:")
            print(f"   - Verify {langfuse_host} is accessible")
            print("   - Check network connectivity and firewall settings")
        else:
            print("\n💡 TROUBLESHOOTING:")
            print("   - Verify your Langfuse instance is running")
            print("   - Check that the credentials are properly formatted")
            print("   - Ensure the Langfuse service is accessible")

        return False


def validate_frontend_langfuse_host():
    """Validate frontend Langfuse host configuration."""
    frontend_host = os.getenv("NEXT_PUBLIC_LANGFUSE_HOST", "")

    if frontend_host and frontend_host != ALLOWED_LANGFUSE_HOST:
        print("❌ FRONTEND LANGFUSE SECURITY ERROR: Unauthorized frontend host detected")
        print(f"   Configured NEXT_PUBLIC_LANGFUSE_HOST: {frontend_host}")
        print(f"   Allowed host: {ALLOWED_LANGFUSE_HOST}")
        print("\n🛡️ SECURITY PROTECTION:")
        print("   This prevents frontend from sending traces to unauthorized instances.")
        print("\n💡 SOLUTION:")
        print(f"   Set NEXT_PUBLIC_LANGFUSE_HOST={ALLOWED_LANGFUSE_HOST}")
        return False

    if frontend_host:
        print(f"✅ Frontend Langfuse host validation passed: {frontend_host}")
    else:
        print("NEXT_PUBLIC_LANGFUSE_HOST not set (will use fallback)")

    return True


def main():
    """Main validation function."""
    print("🚀 Starting Langfuse Configuration Validation...")
    print("=" * 60)

    # Skip validation in CI/CD environments
    if is_ci_environment():
        print("🔄 CI/CD ENVIRONMENT DETECTED")
        print("   Skipping Langfuse validation during build.")
        print("   Langfuse credentials will be validated at runtime in deployed environment.")
        print("✅ BUILD VALIDATION PASSED (CI/CD mode)")
        sys.exit(0)

    # Track validation results
    validations = [
        ("Environment Variables", validate_environment_variables),
        ("Langfuse Host Security", validate_langfuse_host),
        ("Frontend Host Security", validate_frontend_langfuse_host),
        ("Langfuse Connection", validate_langfuse_connection),
    ]

    failed_validations = []

    for validation_name, validation_func in validations:
        print(f"\n📋 {validation_name}:")
        try:
            if not validation_func():
                failed_validations.append(validation_name)
        except Exception as e:
            print(f"❌ {validation_name} failed with exception: {e!s}")
            failed_validations.append(validation_name)

    print("\n" + "=" * 60)

    if failed_validations:
        print("❌ LANGFUSE CONFIGURATION VALIDATION FAILED")
        print(f"   Failed validations: {', '.join(failed_validations)}")
        print("\n🔧 ACTION REQUIRED:")
        print("   Fix the Langfuse configuration issues above before deploying.")
        print("   This prevents accidental data leakage to unauthorized systems.")
        sys.exit(1)
    else:
        print("✅ ALL LANGFUSE CONFIGURATION VALIDATIONS PASSED")
        print("   Your Langfuse configuration is secure and ready for deployment!")
        sys.exit(0)


if __name__ == "__main__":
    main()
