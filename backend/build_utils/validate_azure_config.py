#!/usr/bin/env python3
# ruff: noqa: T201,E402,EXE001
"""
Azure Configuration Validation Script

This script validates Azure Storage configuration during Docker build time
to catch configuration issues early and provide helpful error messages in logs.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path for imports
backend_dir = Path(__file__).parent.parent  # Go up one level from build_utils to backend
sys.path.insert(0, str(backend_dir))

from app.audio.azure_utils import validate_azure_storage_config


def is_ci_environment():
    """Check if we're running in a CI/CD environment."""
    ci_indicators = [
        "CI",
        "CONTINUOUS_INTEGRATION",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "TF_BUILD",  # Azure DevOps
    ]
    return any(os.getenv(indicator) for indicator in ci_indicators)


def validate_environment_variables():
    """Validate that required environment variables are present."""
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


def validate_connection_string_format():
    """Validate the connection string format and extract components."""
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


def main():
    """Main validation function."""
    print("🚀 Starting Azure Configuration Validation...")
    print("=" * 60)

    # Skip validation in CI/CD environments
    if is_ci_environment():
        print("🔄 CI/CD ENVIRONMENT DETECTED")
        print("   Skipping Azure validation during build.")
        print("   Azure credentials will be validated at runtime in deployed environment.")
        print("✅ BUILD VALIDATION PASSED (CI/CD mode)")
        sys.exit(0)

    # Track validation results
    validations = [
        ("Environment Variables", validate_environment_variables),
        ("Connection String Format", validate_connection_string_format),
        ("Azure Storage Access", validate_azure_storage),
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
        print("❌ AZURE CONFIGURATION VALIDATION FAILED")
        print(f"   Failed validations: {', '.join(failed_validations)}")
        print("\n🔧 ACTION REQUIRED:")
        print("   Fix the Azure configuration issues above before deploying.")
        print("   This will prevent runtime errors and service outages.")
        sys.exit(1)
    else:
        print("✅ ALL AZURE CONFIGURATION VALIDATIONS PASSED")
        print("   Your Azure Storage configuration is ready for deployment!")
        sys.exit(0)


if __name__ == "__main__":
    main()
