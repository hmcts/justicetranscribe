# Copyright (c) HashiCorp, Inc.
# SPDX-License-Identifier: MPL-2.0

# Frontend outputs
output "frontend_app_name" {
  description = "Name of the frontend web app"
  value       = azurerm_linux_web_app.frontend.name
}

output "frontend_app_url" {
  description = "URL of the frontend application"
  value       = "https://${azurerm_linux_web_app.frontend.default_hostname}"
}

# Backend API outputs
output "backend_api_name" {
  description = "Name of the backend API app service"
  value       = azurerm_linux_web_app.backend_api.name
}

output "backend_api_url" {
  description = "URL of the backend API"
  value       = "https://${azurerm_linux_web_app.backend_api.default_hostname}"
}

output "backend_api_docs_url" {
  description = "URL of the backend API documentation"
  value       = "https://${azurerm_linux_web_app.backend_api.default_hostname}/docs"
}

# Add these outputs for the GitHub workflow
output "acr_login_server" {
  value = azurerm_container_registry.acr.login_server
}

# Legacy output name for backward compatibility during transition
output "app_service_name" {
  description = "Name of the frontend app service (legacy name for compatibility)"
  value       = azurerm_linux_web_app.frontend.name
}

# Updated output names
output "frontend_service_name" {
  description = "Name of the frontend app service"
  value       = azurerm_linux_web_app.frontend.name
}

output "backend_service_name" {
  description = "Name of the backend app service"
  value       = azurerm_linux_web_app.backend_api.name
}

output "acr_admin_username" {
  value = azurerm_container_registry.acr.admin_username
}

output "webhook_url" {
  description = "Webhook URL for the frontend app"
  value       = "https://${azurerm_linux_web_app.frontend.site_credential[0].name}:${azurerm_linux_web_app.frontend.site_credential[0].password}@${azurerm_linux_web_app.frontend.name}.scm.azurewebsites.net/api/registry/webhook"
  sensitive   = true
}

# Outputs for GitHub Actions OIDC authentication
output "github_actions_client_id" {
  description = "Client ID of the GitHub Actions managed identity"
  value       = azurerm_user_assigned_identity.github_actions.client_id
}

output "github_actions_tenant_id" {
  description = "Tenant ID for the GitHub Actions managed identity"
  value       = azurerm_user_assigned_identity.github_actions.tenant_id
}

output "subscription_id" {
  description = "Azure subscription ID"
  value       = data.azurerm_client_config.current.subscription_id
}

# Authentication outputs
output "auth_callback_url" {
  description = "Authentication callback URL (provide this to security team for app registration)"
  value       = "https://${azurerm_linux_web_app.frontend.default_hostname}/.auth/login/aad/callback"
}


# Instructions for manual secret setup
output "deployment_summary" {
  description = "Summary of deployed services and URLs"
  value = <<EOF
Successfully deployed:

🌐 Frontend App: https://${azurerm_linux_web_app.frontend.default_hostname}
🔌 Backend API: https://${azurerm_linux_web_app.backend_api.default_hostname}
📚 API Documentation: https://${azurerm_linux_web_app.backend_api.default_hostname}/docs
🗄️ PostgreSQL Database: ${azurerm_postgresql_flexible_server.main.fqdn}


EOF
}

# Add this new output for the backend hostname
output "backend_hostname" {
  description = "Backend API hostname for building frontend"
  value       = local.backend_hostname
}

# Database outputs
output "postgres_server_name" {
  description = "Name of the PostgreSQL server"
  value       = azurerm_postgresql_flexible_server.main.name
}

output "postgres_server_fqdn" {
  description = "FQDN of the PostgreSQL server"
  value       = azurerm_postgresql_flexible_server.main.fqdn
}

output "postgres_database_name" {
  description = "Name of the PostgreSQL database"
  value       = azurerm_postgresql_flexible_server_database.main.name
}

output "database_connection_string" {
  description = "Database connection string (sensitive)"
  value       = local.database_connection_string
  sensitive   = true
}