# Copyright (c) HashiCorp, Inc.
# SPDX-License-Identifier: MPL-2.0

terraform {
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "tfstatejusticeaiunitjust"
    container_name       = "tfstate"
    # key will be set dynamically via -backend-config in the workflow
  }

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.azure_subscription_id
}

# Local values for environment-aware naming
locals {
  environment_prefix = "${var.prefix}-${var.environment}"
  frontend_app_name  = "${var.prefix}-${var.environment}-frontend"
  backend_api_name   = "${var.prefix}-${var.environment}-backend-api"
  
  # Calculate URLs without creating circular dependencies
  frontend_hostname = "${local.frontend_app_name}.azurewebsites.net"
  backend_hostname  = "${local.backend_api_name}.azurewebsites.net"
}

resource "azurerm_resource_group" "main" {
  name     = "${local.environment_prefix}-resources"
  location = var.location

  tags = {
    Environment = var.environment
    Project     = var.prefix
  }
}

# Virtual Network for secure communication
resource "azurerm_virtual_network" "main" {
  name                = "${local.environment_prefix}-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  tags = {
    Environment = var.environment
    Project     = var.prefix
  }
}

# Subnet for App Services
resource "azurerm_subnet" "app_services" {
  name                 = "${local.environment_prefix}-app-services-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.1.0/24"]

  delegation {
    name = "app-service-delegation"
    service_delegation {
      name    = "Microsoft.Web/serverFarms"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/action",
      ]
    }
  }
}

# Subnet for PostgreSQL
resource "azurerm_subnet" "database" {
  name                 = "${local.environment_prefix}-database-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.2.0/24"]

  delegation {
    name = "postgresql-delegation"
    service_delegation {
      name    = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
      ]
    }
  }
}

# Private DNS zone for PostgreSQL - fix the naming
resource "azurerm_private_dns_zone" "postgres" {
  name                = "privatelink.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.main.name

  tags = {
    Environment = var.environment
    Project     = var.prefix
  }
}

# Link private DNS zone to VNet
resource "azurerm_private_dns_zone_virtual_network_link" "postgres" {
  name                  = "${local.environment_prefix}-postgres-vnet-link"
  resource_group_name   = azurerm_resource_group.main.name
  private_dns_zone_name = azurerm_private_dns_zone.postgres.name
  virtual_network_id    = azurerm_virtual_network.main.id
  registration_enabled  = true

  tags = {
    Environment = var.environment
    Project     = var.prefix
  }
}

resource "azurerm_service_plan" "main" {
  name                = "${local.environment_prefix}-sp-zipdeploy"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            = "S1"

  tags = {
    Environment = var.environment
    Project     = var.prefix
  }
}

resource "azurerm_container_registry" "acr" {
  name                = "${var.prefix}${var.environment}acr"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Standard"
  admin_enabled       = true

  tags = {
    Environment = var.environment
    Project     = var.prefix
  }
}

resource "azurerm_linux_web_app" "frontend" {
  name                = local.frontend_app_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.main.id

  app_settings = {
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false"
    "ENVIRONMENT"                         = var.environment
    
    # Frontend environment variables
    "NEXT_PUBLIC_API_URL"                        = "https://${local.backend_hostname}"
    "EXTERNAL_API_KEY"                          = "placeholder-external-api-key"
    "MICROSOFT_PROVIDER_AUTHENTICATION_SECRET" = "placeholder-auth-client-secret"
    
    # Add database connection for Next.js API routes
    "DATABASE_CONNECTION_STRING"                = local.database_connection_string
    "DATABASE_URL"                              = local.database_connection_string  # Alternative naming
  }

  # VNet integration allows secure database access
  virtual_network_subnet_id = azurerm_subnet.app_services.id

  # Add this lifecycle rule to ignore changes to app_settings
  lifecycle {
    ignore_changes = [
      app_settings
    ]
  }

  # Authentication is always enabled
  auth_settings_v2 {
    auth_enabled           = true
    require_authentication = true
    unauthenticated_action = "RedirectToLoginPage"
    default_provider       = "azureactivedirectory"
    
    active_directory_v2 {
      client_id                    = var.auth_client_id
      tenant_auth_endpoint         = "https://login.microsoftonline.com/${var.auth_tenant_id}/v2.0/"
       client_secret_setting_name = "MICROSOFT_PROVIDER_AUTHENTICATION_SECRET"
    }
    
    login {
      token_store_enabled           = true
      token_refresh_extension_time  = 168    # 7 days (168 hours)
      allowed_external_redirect_urls = [
        "https://${local.frontend_hostname}",
        "https://${local.frontend_hostname}/",
         var.custom_domain_url,
        "${var.custom_domain_url}/"
      ]
    }
  }

  site_config {
    application_stack {
      docker_image_name        = "${lower(var.docker_image_name)}:${var.docker_image_tag}"
      docker_registry_url      = "https://${azurerm_container_registry.acr.login_server}"
      docker_registry_username = azurerm_container_registry.acr.admin_username
      docker_registry_password = azurerm_container_registry.acr.admin_password
    }
  }

  tags = {
    Environment = var.environment
    Project     = var.prefix
    Component   = "frontend"
  }
}

# Backend API App Service
resource "azurerm_linux_web_app" "backend_api" {
  name                = local.backend_api_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.main.id

  app_settings = {
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false"
    "ENVIRONMENT"                         = var.environment
    "WEBSITES_PORT"                       = "80"
    
    # FastAPI specific settings
    "PYTHONPATH"                         = "/app"
    
    # CORS allowed origins - include custom domain
    "CORS_ALLOWED_ORIGINS"               = "https://${local.frontend_hostname},${var.custom_domain_url},http://localhost:3000"    
    # Database and external API settings
    "DATABASE_CONNECTION_STRING"         = local.database_connection_string
    "EXTERNAL_API_KEY"                  = "placeholder-external-api-key"
    "MICROSOFT_PROVIDER_AUTHENTICATION_SECRET" = "placeholder-auth-client-secret"

     # Add authentication configuration
    "AUTH_CLIENT_ID"    = var.auth_client_id
    "AUTH_TENANT_ID"    = var.auth_tenant_id
    "AUTH_ISSUER_URL"   = "https://login.microsoftonline.com/${var.auth_tenant_id}/v2.0"
    
    # Application configuration
    "APP_URL"                           = "https://${local.frontend_hostname}"
    
    # AWS Configuration
    "AWS_REGION"                        = "eu-west-2"
    "AWS_ACCOUNT_ID"                    = "placeholder-aws-account-id"
    "DATA_S3_BUCKET"                    = "i-dot-ai-dev-justice-transcribe-data"
    
    # Azure AI Services
    "AZURE_OPENAI_API_KEY"              = "placeholder-azure-openai-api-key"
    "AZURE_OPENAI_ENDPOINT"             = "placeholder-azure-openai-endpoint"
    "AZURE_GROK_API_KEY"                = "placeholder-azure-grok-api-key"
    "AZURE_GROK_ENDPOINT"               = "placeholder-azure-grok-endpoint"
    "AZURE_SPEECH_KEY"                  = "placeholder-azure-speech-key"
    "AZURE_SPEECH_REGION"               = "placeholder-azure-speech-region"
    
    # Monitoring and Observability
    "SENTRY_DSN"                        = "placeholder-sentry-dsn"
    "LANGFUSE_SECRET_KEY"               = "placeholder-langfuse-secret-key"
    "LANGFUSE_PUBLIC_KEY"               = "placeholder-langfuse-public-key"
    "LANGFUSE_HOST"                     = "placeholder-langfuse-host"
    
    # Government Services
    "GOV_NOTIFY_API_KEY"                = "placeholder-gov-notify-api-key"
    
    # Development/Testing Configuration
    "DISABLE_AUTH_SIGNATURE_VERIFICATION" = "false"
    "GOOGLE_APPLICATION_CREDENTIALS_JSON_OBJECT" = "placeholder-google-credentials-json"
  }

  # Only ignore changes to sensitive environment variables
  lifecycle {
    ignore_changes = [
      app_settings["MICROSOFT_PROVIDER_AUTHENTICATION_SECRET"],
      app_settings["EXTERNAL_API_KEY"],
      app_settings["AZURE_OPENAI_API_KEY"],
      app_settings["AZURE_OPENAI_ENDPOINT"],
      app_settings["AZURE_GROK_API_KEY"],
      app_settings["AZURE_GROK_ENDPOINT"],
      app_settings["AZURE_SPEECH_KEY"],
      app_settings["AZURE_SPEECH_REGION"],
      app_settings["SENTRY_DSN"],
      app_settings["LANGFUSE_SECRET_KEY"],
      app_settings["LANGFUSE_PUBLIC_KEY"],
      app_settings["LANGFUSE_HOST"],
      app_settings["GOV_NOTIFY_API_KEY"],
      app_settings["AWS_ACCOUNT_ID"],
      app_settings["GOOGLE_APPLICATION_CREDENTIALS_JSON_OBJECT"],
    ]
  }

  # Authentication is always enabled for internal apps - all routes require authentication
  auth_settings_v2 {
    auth_enabled           = true
    require_authentication = true
    unauthenticated_action = "Return401"  # Changed from RedirectToLoginPage
    default_provider       = "azureactivedirectory"
    
    active_directory_v2 {
      client_id                    = var.auth_client_id
      tenant_auth_endpoint         = "https://login.microsoftonline.com/${var.auth_tenant_id}/v2.0/"
      client_secret_setting_name   = "MICROSOFT_PROVIDER_AUTHENTICATION_SECRET"
    }
    
    login {
      token_store_enabled           = true
      token_refresh_extension_time  = 168    # 7 days (168 hours)
      allowed_external_redirect_urls = [
        "https://${local.frontend_hostname}",
        "https://${local.frontend_hostname}/",
        var.custom_domain_url,
        "${var.custom_domain_url}/"
      ]
    }
  }

  site_config {
    application_stack {
      docker_image_name        = "${lower(var.backend_docker_image_name)}:${var.backend_docker_image_tag}"
      docker_registry_url      = "https://${azurerm_container_registry.acr.login_server}"
      docker_registry_username = azurerm_container_registry.acr.admin_username
      docker_registry_password = azurerm_container_registry.acr.admin_password
    }

    # Health check configuration - both parameters are required
    health_check_path                = "/health"
    health_check_eviction_time_in_min = 2

    # CORS configuration - include custom domain
    cors {
      allowed_origins     = ["https://${local.frontend_hostname}", var.custom_domain_url]      
      support_credentials = true
    }
  }

  # Enable logging
  logs {
    detailed_error_messages = true
    failed_request_tracing  = true
    
    http_logs {
      file_system {
        retention_in_days = 7
        retention_in_mb   = 50
      }
    }
  }

  # Add VNet integration
  virtual_network_subnet_id = azurerm_subnet.app_services.id

  tags = {
    Environment = var.environment
    Project     = var.prefix
    Component   = "backend-api"
  }
}

# Create user-assigned managed identity for GitHub Actions
resource "azurerm_user_assigned_identity" "github_actions" {
  name                = "${local.environment_prefix}-github-actions-identity"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  tags = {
    Environment = var.environment
    Project     = var.prefix
  }
}

# Assign Contributor role to the managed identity for the subscription
resource "azurerm_role_assignment" "github_actions_contributor" {
  scope                = "/subscriptions/${data.azurerm_client_config.current.subscription_id}"
  role_definition_name = "Contributor"
  principal_id         = azurerm_user_assigned_identity.github_actions.principal_id
}

# Assign AcrPush role to the managed identity for the container registry
resource "azurerm_role_assignment" "github_actions_acr_push" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPush"
  principal_id         = azurerm_user_assigned_identity.github_actions.principal_id
}

# Get current Azure configuration
data "azurerm_client_config" "current" {}

# Generate secure random password for PostgreSQL
resource "random_password" "postgres_password" {
  length  = 32
  special = true
  upper   = true
  lower   = true
  numeric = true
  
  # Ensure password contains at least one of each character type
  min_special = 4
  min_upper   = 4
  min_lower   = 4
  min_numeric = 4
  
  # Exclude characters that can cause issues in connection strings
  override_special = "!#%&*+-/=?^_`|~"
}

# PostgreSQL Flexible Server
resource "azurerm_postgresql_flexible_server" "main" {
  name                         = "${local.environment_prefix}-postgres"
  resource_group_name          = azurerm_resource_group.main.name
  location                     = azurerm_resource_group.main.location
  version                      = var.postgres_version
  administrator_login          = var.postgres_admin_username
  administrator_password       = random_password.postgres_password.result
  zone                         = "1"
  storage_mb                   = var.postgres_storage_mb
  sku_name                     = var.postgres_sku_name
  backup_retention_days        = 7
  geo_redundant_backup_enabled = false

  # VNet Integration - more secure
  delegated_subnet_id    = azurerm_subnet.database.id
  private_dns_zone_id    = azurerm_private_dns_zone.postgres.id
  public_network_access_enabled = false

  # Ensure the private DNS zone link is created first
  depends_on = [azurerm_private_dns_zone_virtual_network_link.postgres]

  authentication {
    active_directory_auth_enabled = true
    password_auth_enabled         = true
  }
  
  tags = {
    Environment = var.environment
    Project     = var.prefix
    Component   = "database"
  }
}

# PostgreSQL Database
resource "azurerm_postgresql_flexible_server_database" "main" {
  name      = var.postgres_database_name
  server_id = azurerm_postgresql_flexible_server.main.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

# Create database connection string
locals {
  database_connection_string = "postgresql://${var.postgres_admin_username}:${urlencode(random_password.postgres_password.result)}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/${var.postgres_database_name}?sslmode=require"
}

# Map branch names to environments
locals {
  branch_to_env = {
    "main"    = "prod"
    "dev"     = "dev" 
    "preprod" = "preprod"
  }
}

# Configure federated identity credential for main branch (prod)
resource "azurerm_federated_identity_credential" "github_actions_main" {
  name                = "${local.environment_prefix}-github-main-branch"
  resource_group_name = azurerm_resource_group.main.name
  audience            = ["api://AzureADTokenExchange"]
  issuer              = "https://token.actions.githubusercontent.com"
  parent_id           = azurerm_user_assigned_identity.github_actions.id
  subject             = "repo:${var.github_repository}:ref:refs/heads/main"
}

# Configure federated identity credential for dev branch
resource "azurerm_federated_identity_credential" "github_actions_dev" {
  count               = var.environment == "dev" ? 1 : 0
  name                = "${local.environment_prefix}-github-dev-branch"
  resource_group_name = azurerm_resource_group.main.name
  audience            = ["api://AzureADTokenExchange"]
  issuer              = "https://token.actions.githubusercontent.com"
  parent_id           = azurerm_user_assigned_identity.github_actions.id
  subject             = "repo:${var.github_repository}:ref:refs/heads/dev"
}

# Configure federated identity credential for preprod branch
resource "azurerm_federated_identity_credential" "github_actions_preprod" {
  count               = var.environment == "preprod" ? 1 : 0
  name                = "${local.environment_prefix}-github-preprod-branch"
  resource_group_name = azurerm_resource_group.main.name
  audience            = ["api://AzureADTokenExchange"]
  issuer              = "https://token.actions.githubusercontent.com"
  parent_id           = azurerm_user_assigned_identity.github_actions.id
  subject             = "repo:${var.github_repository}:ref:refs/heads/preprod"
}

# Configure federated identity credential for pull requests (optional)
resource "azurerm_federated_identity_credential" "github_actions_pr" {
  name                = "${local.environment_prefix}-github-pull-requests"
  resource_group_name = azurerm_resource_group.main.name
  audience            = ["api://AzureADTokenExchange"]
  issuer              = "https://token.actions.githubusercontent.com"
  parent_id           = azurerm_user_assigned_identity.github_actions.id
  subject             = "repo:${var.github_repository}:pull_request"
}
