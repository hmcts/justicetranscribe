#!/bin/bash

# Simple Azure Backend Setup for justicetranscribe
set -e

# Configuration
RESOURCE_GROUP="terraform-state-rg"
STORAGE_ACCOUNT="tfstatejusticeaiunitjust"
CONTAINER_NAME="tfstate"
LOCATION="uksouth"
SUBSCRIPTION_ID="ef9f1e98-5f6a-481c-b6b6-c632e4998827"

echo "🚀 Setting up Azure backend for justicetranscribe"

# Check Azure CLI
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Install it first: brew install azure-cli"
    exit 1
fi

# Check login
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure. Run: az login"
    exit 1
fi

echo "✅ Azure CLI ready"

# Check for subscription ID
if [ -z "$SUBSCRIPTION_ID" ]; then
    echo "❌ Azure subscription ID is not set. Please provide 'azure_subscription_id' when running cookiecutter."
    exit 1
fi

# Set subscription
echo "🔍 Setting active Azure subscription to '$SUBSCRIPTION_ID'..."
if ! az account set --subscription "$SUBSCRIPTION_ID" > /dev/null; then
    echo "❌ Failed to set subscription. Make sure you have access to this subscription."
    exit 1
fi

# Create resource group
echo "📦 Creating resource group..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none 2>/dev/null || echo "Resource group already exists"

# Create storage account
echo "💾 Creating storage account..."
if ! output=$(az storage account create \
  --name "$STORAGE_ACCOUNT" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku Standard_LRS \
  --output none 2>&1); then
    echo "⚠️  Storage account creation failed: $output"
    echo "Continuing anyway (may already exist)..."
fi

# Create container
echo "📁 Creating container..."
az storage container create \
  --name "$CONTAINER_NAME" \
  --account-name "$STORAGE_ACCOUNT" \
  --output none 2>/dev/null || echo "Container already exists"