#!/usr/bin/env python3
# ruff: noqa: T201
"""
Unified Configuration Validation Script

This script validates both Azure Storage and Langfuse configuration during Docker build time
to catch configuration issues early and provide helpful error messages in logs.

Combines validation logic from validate_azure_config.py and validate_langfuse_config.py
into a single, comprehensive validation process.
"""

import os
import sys

from langfuse import Langfuse

from app.audio.azure_utils import validate_azure_storage_config

# The only allowed Langfuse host for Justice AI Unit
ALLOWED_LANGFUSE_HOST = "https://langfuse-ai.justice.gov.uk"


def is_ci_environment():
    """Check if we're running in a CI/CD environment."""
    ci_indicators = [
        "CI",
        "CONTINUOUS_INTEGRATION",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "TF_BUILD",  # Azure DevOps
        "AZURE_DEVOPS",
        "BUILD_BUILDID",
    ]
    return any(os.getenv(indicator) for indicator in ci_indicators)


# =============================================================================
# AZURE VALIDATION FUNCTIONS
# =============================================================================


def validate_azure_environment_variables():
    """Validate that required Azure environment variables are present."""
    required_vars = ["AZURE_STORAGE_CONNECTION_STRING", "AZURE_STORAGE_ACCOUNT_NAME", "AZURE_STORAGE_CONTAINER_NAME"]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("❌ AZURE CONFIGURATION ERROR: Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 SOLUTION: Ensure these environment variables are set in your:")
        print("   - .env file (for local development)")
        print("   - Docker environment configuration")
        print("   - Terraform/infrastructure configuration")
        return False

    print("✅ All required Azure environment variables are present")
    return True


def validate_azure_connection_string_format():
    """Validate the Azure Storage connection string format and extract components."""
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")

    if not connection_string:
        print("❌ AZURE CONFIGURATION ERROR: AZURE_STORAGE_CONNECTION_STRING is empty")
        return False

    # Basic format validation
    required_parts = ["AccountName=", "AccountKey="]
    for part in required_parts:
        if part not in connection_string:
            print(f"❌ AZURE CONFIGURATION ERROR: Connection string missing {part}")
            return False

    print("✅ Azure Storage connection string format appears valid")
    return True


def validate_azure_storage():
    """Validate Azure Storage configuration using our azure_utils logic."""
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")

    try:
        print("🔍 Validating Azure Storage configuration...")
        result = validate_azure_storage_config(connection_string)

        if result["valid"]:
            print("✅ Azure Storage configuration is valid and accessible")
            return True
        else:
            print("❌ AZURE STORAGE VALIDATION FAILED:")
            print(f"   Error: {result.get('error', 'Unknown error')}")

            # Provide specific guidance based on the error
            error_msg = result.get("error", "").lower()
            if "account name" in error_msg:
                print("\n💡 POSSIBLE SOLUTIONS:")
                print("   - Check that the AccountName in your connection string is correct")
                print("   - Verify the storage account exists in your Azure subscription")
                print("   - Ensure the account name matches AZURE_STORAGE_ACCOUNT_NAME environment variable")
            elif "account key" in error_msg or "invalid" in error_msg:
                print("\n💡 POSSIBLE SOLUTIONS:")
                print("   - Check that the AccountKey in your connection string is current")
                print("   - The storage account key may have been rotated - update with the latest key")
                print("   - Verify you're using the correct storage account (primary vs secondary key)")
                print("   - Check Azure portal > Storage Account > Access Keys for the current keys")
            else:
                print("\n💡 TROUBLESHOOTING:")
                print("   - Verify your Azure Storage account is accessible")
                print("   - Check network connectivity and firewall settings")
                print("   - Ensure the storage account is in the correct Azure region")

            return False

    except Exception as e:
        print("❌ AZURE STORAGE VALIDATION ERROR:")
        print(f"   Exception: {e!s}")
        print("\n💡 TROUBLESHOOTING:")
        print("   - Check if Azure Storage libraries are properly installed")
        print("   - Verify network connectivity to Azure services")
        print("   - Review the connection string format and credentials")
        return False


# =============================================================================
# LANGFUSE VALIDATION FUNCTIONS
# =============================================================================


def validate_langfuse_environment_variables():
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

    print("✅ All required Langfuse environment variables are present")
    return True


def validate_langfuse_host():
    """Validate that only the approved Justice AI Unit Langfuse instance is used."""
    langfuse_host = os.getenv("LANGFUSE_HOST", "").strip()

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
    """Validate connection and authentication to Langfuse instance."""
    langfuse_host = os.getenv("LANGFUSE_HOST", "").strip()
    langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "").strip()
    langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY", "").strip()

    try:
        print("🔍 Validating Langfuse connection and authentication...")

        client = Langfuse(
            public_key=langfuse_public_key,
            secret_key=langfuse_secret_key,
            host=langfuse_host,
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
    """Validate that frontend environment variables are properly configured."""
    frontend_host = os.getenv("NEXT_PUBLIC_LANGFUSE_HOST", "").strip()

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


# =============================================================================
# MAIN VALIDATION ORCHESTRATION
# =============================================================================


def main():
    """Main validation function."""
    print("🚀 Starting Configuration Validation...")
    print("=" * 60)

    # Skip validation in CI/CD environments
    if is_ci_environment():
        print("🔄 CI/CD ENVIRONMENT DETECTED")
        print("   Skipping configuration validation during build.")
        print("   Configuration will be validated at runtime in deployed environment.")
        print("✅ BUILD VALIDATION PASSED (CI/CD mode)")
        sys.exit(0)

    # Track validation results
    validations = [
        # Azure validations
        ("Azure Environment Variables", validate_azure_environment_variables),
        ("Azure Connection String Format", validate_azure_connection_string_format),
        ("Azure Storage Access", validate_azure_storage),
        # Langfuse validations
        ("Langfuse Environment Variables", validate_langfuse_environment_variables),
        ("Langfuse Host Security", validate_langfuse_host),
        ("Frontend Langfuse Host Security", validate_frontend_langfuse_host),
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
        print("❌ CONFIGURATION VALIDATION FAILED")
        print(f"   Failed validations: {', '.join(failed_validations)}")
        print("\n🔧 ACTION REQUIRED:")
        print("   Fix the configuration issues above before deploying.")
        print("   This prevents runtime errors and accidental data leakage.")
        sys.exit(1)
    else:
        print("✅ ALL CONFIGURATION VALIDATIONS PASSED")
        print("   Your Azure and Langfuse configurations are secure and ready for deployment!")
        sys.exit(0)


if __name__ == "__main__":
    main()
