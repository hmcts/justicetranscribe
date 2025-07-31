#!/bin/bash
# save as: scripts/restore-terraform-state.sh

set -e

ENV=${1:-dev}
SUBSCRIPTION_ID="ef9f1e98-5f6a-481c-b6b6-c632e4998827"

echo "🔄 Restoring Terraform state for environment: $ENV"

# Basic checks...
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Install it first: brew install azure-cli"
    exit 1
fi

if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure. Run: az login"
    exit 1
fi

az account set --subscription "$SUBSCRIPTION_ID"

RESOURCE_GROUP="justicetranscribe-${ENV}-resources"
if ! az group show --name "$RESOURCE_GROUP" &>/dev/null; then
    echo "❌ Resource group $RESOURCE_GROUP not found!"
    exit 1
fi

# Step 1: Recreate state backend
echo "📦 Setting up Terraform state backend..."
cd "$(dirname "$0")"
./setup-azure-backend.sh

# Step 2: Initialize Terraform
echo "🔧 Initializing Terraform..."
cd ../infrastructure
terraform init -reconfigure -backend-config="key=${ENV}.terraform.tfstate"

# Step 3: Import everything EXCEPT random_password
echo "📥 Importing Terraform resources (excluding password)..."

import_resource() {
    local tf_resource="$1"
    local azure_id="$2"
    
    # Check if resource already exists in state
    if terraform state show "$tf_resource" &>/dev/null; then
        echo "  ✅ $tf_resource (already imported)"
        return 0
    fi
    
    echo "  🔄 Importing $tf_resource..."
    if terraform import -var-file="${ENV}.tfvars" "$tf_resource" "$azure_id"; then
        echo "  ✅ Successfully imported $tf_resource"
    else
        echo "  ⚠️  Failed to import $tf_resource"
        return 1
    fi
}

# Import all resources
import_resource "azurerm_resource_group.main" \
    "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}"

import_resource "azurerm_virtual_network.main" \
    "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.Network/virtualNetworks/justicetranscribe-${ENV}-vnet"

import_resource "azurerm_subnet.app_services" \
    "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.Network/virtualNetworks/justicetranscribe-${ENV}-vnet/subnets/justicetranscribe-${ENV}-app-services-subnet"

import_resource "azurerm_subnet.database" \
    "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.Network/virtualNetworks/justicetranscribe-${ENV}-vnet/subnets/justicetranscribe-${ENV}-database-subnet"

import_resource "azurerm_private_dns_zone.postgres" \
    "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.Network/privateDnsZones/privatelink.postgres.database.azure.com"

import_resource "azurerm_private_dns_zone_virtual_network_link.postgres" \
    "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.Network/privateDnsZones/privatelink.postgres.database.azure.com/virtualNetworkLinks/justicetranscribe-${ENV}-postgres-vnet-link"

import_resource "azurerm_service_plan.main" \
    "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.Web/serverFarms/justicetranscribe-${ENV}-sp-zipdeploy"

import_resource "azurerm_container_registry.acr" \
    "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.ContainerRegistry/registries/justicetranscribe${ENV}acr"

import_resource "azurerm_linux_web_app.frontend" \
    "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.Web/sites/justicetranscribe-${ENV}-frontend"

import_resource "azurerm_linux_web_app.backend_api" \
    "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.Web/sites/justicetranscribe-${ENV}-backend-api"

import_resource "azurerm_user_assigned_identity.github_actions" \
    "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/justicetranscribe-${ENV}-github-actions-identity"

import_resource "azurerm_postgresql_flexible_server.main" \
    "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.DBforPostgreSQL/flexibleServers/justicetranscribe-${ENV}-postgres"

import_resource "azurerm_postgresql_flexible_server_database.main" \
    "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.DBforPostgreSQL/flexibleServers/justicetranscribe-${ENV}-postgres/databases/justicetranscribe_db"

# Import role assignments (need to find their actual IDs)
echo "🔍 Finding role assignment IDs..."
PRINCIPAL_ID=$(az identity show --name "justicetranscribe-${ENV}-github-actions-identity" --resource-group "${RESOURCE_GROUP}" --query principalId -o tsv)

# Get role assignment IDs
CONTRIBUTOR_ROLE_ID=$(az role assignment list --assignee "$PRINCIPAL_ID" --role "Contributor" --scope "/subscriptions/${SUBSCRIPTION_ID}" --query "[0].id" -o tsv)
ACR_ROLE_ID=$(az role assignment list --assignee "$PRINCIPAL_ID" --role "AcrPush" --scope "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.ContainerRegistry/registries/justicetranscribe${ENV}acr" --query "[0].id" -o tsv)

if [ -n "$CONTRIBUTOR_ROLE_ID" ]; then
    import_resource "azurerm_role_assignment.github_actions_contributor" "$CONTRIBUTOR_ROLE_ID"
fi

if [ -n "$ACR_ROLE_ID" ]; then
    import_resource "azurerm_role_assignment.github_actions_acr_push" "$ACR_ROLE_ID"
fi

# Import federated identity credentials
import_resource "azurerm_federated_identity_credential.github_actions_main" \
    "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/justicetranscribe-${ENV}-github-actions-identity/federatedIdentityCredentials/justicetranscribe-${ENV}-github-main-branch"

# Only import dev federated credential for dev environment
if [ "$ENV" = "dev" ]; then
    import_resource "azurerm_federated_identity_credential.github_actions_dev[0]" \
        "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/justicetranscribe-${ENV}-github-actions-identity/federatedIdentityCredentials/justicetranscribe-${ENV}-github-dev-branch"
fi

# Only import preprod federated credential for preprod environment  
if [ "$ENV" = "preprod" ]; then
    import_resource "azurerm_federated_identity_credential.github_actions_preprod[0]" \
        "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/justicetranscribe-${ENV}-github-actions-identity/federatedIdentityCredentials/justicetranscribe-${ENV}-github-preprod-branch"
fi

import_resource "azurerm_federated_identity_credential.github_actions_pr" \
    "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/justicetranscribe-${ENV}-github-actions-identity/federatedIdentityCredentials/justicetranscribe-${ENV}-github-pull-requests"

# NOTE: We deliberately skip random_password.postgres_password - let Terraform create it

echo ""
echo "🎉 Import completed!"
echo ""
echo "Next steps:"
echo "1. Run: terraform plan -var-file=\"${ENV}.tfvars\""
echo "   (This will show it wants to create a new password and update the database)"
echo "2. Run: terraform apply -var-file=\"${ENV}.tfvars\""
echo "   (This will generate new password and update everything automatically)"
echo ""
echo "✨ Terraform will handle the password reset for you!"