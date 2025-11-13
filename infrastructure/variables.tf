# Copyright (c) HashiCorp, Inc.
# SPDX-License-Identifier: MPL-2.0

variable "prefix" {
  description = "The prefix which should be used for all resources in this deployment"
  type        = string
  default     = "justicetranscribe"
}

variable "environment" {
  description = "The environment name (dev, preprod, prod)"
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["dev", "preprod", "prod"], var.environment)
    error_message = "Environment must be one of: dev, preprod, prod."
  }
}

variable "location" {
  description = "The Azure Region in which all resources in this deployment should be created"
  type        = string
  default     = "uksouth"
}

variable "docker_image_repository" {
  description = "The repository path for the Docker image (e.g., justicetranscribe)"
  type        = string
  default     = "justicetranscribe"
}

variable "docker_image_name" {
  description = "The name of the docker image (e.g., tenthacademy)"
  type        = string
  default     = "JusticeAIUnit/justicetranscribe"
}

variable "docker_image_tag" {
  description = "The tag of the docker image (e.g., latest)"
  type        = string
}

variable "github_repository" {
  description = "GitHub repository in the format 'owner/repo-name'"
  type        = string
  default     = "JusticeAIUnit/justicetranscribe"
}

variable "azure_subscription_id" {
  description = "The Azure subscription ID"
  type        = string
  default     = "ef9f1e98-5f6a-481c-b6b6-c632e4998827"
}

# Authentication variables (always enabled)
variable "auth_client_id" {
  description = "Client ID of the Azure AD app registration (provided by security team)"
  type        = string
  default     = ""
  sensitive   = true
}


variable "auth_tenant_id" {
  description = "Azure AD tenant ID"
  type        = string
  default     = ""
}

# Application secret variables
variable "database_connection_string" {
  description = "Database connection string"
  type        = string
  default     = ""
  sensitive   = true
}

variable "external_api_key" {
  description = "External API key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "backend_docker_image_name" {
  description = "The name of the backend docker image"
  type        = string
  default     = "JusticeAIUnit/justicetranscribe-backend"
}

variable "backend_docker_image_tag" {
  description = "The tag of the backend docker image"
  type        = string
  default     = "latest"
}

# Database configuration
variable "postgres_admin_username" {
  description = "The administrator username for the PostgreSQL server"
  type        = string
  default     = "psqladmin"
}

variable "postgres_database_name" {
  description = "The name of the PostgreSQL database"
  type        = string
  default     = "justicetranscribe_db"
}

variable "postgres_sku_name" {
  description = "The SKU name for the PostgreSQL flexible server"
  type        = string
  default     = "B_Standard_B1ms"

  validation {
    condition = contains([
      "B_Standard_B1ms", "B_Standard_B2s", "B_Standard_B2ms", "B_Standard_B4ms",
      "GP_Standard_D2s_v3", "GP_Standard_D4s_v3", "GP_Standard_D8s_v3",
      "MO_Standard_E2s_v3", "MO_Standard_E4s_v3", "MO_Standard_E8s_v3"
    ], var.postgres_sku_name)
    error_message = "postgres_sku_name must be a valid PostgreSQL flexible server SKU."
  }
}

variable "postgres_storage_mb" {
  description = "The storage size in MB for the PostgreSQL server"
  type        = number
  default     = 32768

  validation {
    condition     = var.postgres_storage_mb >= 32768 && var.postgres_storage_mb <= 16777216
    error_message = "postgres_storage_mb must be between 32768 MB (32 GB) and 16777216 MB (16 TB)."
  }
}

variable "postgres_version" {
  description = "The version of PostgreSQL to use"
  type        = string
  default     = "16"

  validation {
    condition     = contains(["11", "12", "13", "14", "15", "16"], var.postgres_version)
    error_message = "postgres_version must be one of: 11, 12, 13, 14, 15, 16."
  }
}

variable "postgres_allowed_ips" {
  description = "List of IP addresses allowed to connect to PostgreSQL (optional)"
  type        = list(string)
  default     = []
}

variable "custom_domain_url" {
  description = "Custom domain URL for allowed redirects and CORS origins"
  type        = string
  default     = "https://transcription.service.justice.gov.uk"
}

# Service Plan configuration
variable "frontend_service_plan_sku" {
  description = "The SKU name for the Frontend App Service Plan"
  type        = string
  default     = "S2"

  validation {
    condition = contains([
      "S1", "S2", "S3",       # Standard tier
      "P1v2", "P2v2", "P3v2", # Premium V2 tier  
      "P1v3", "P2v3", "P3v3", # Premium V3 tier
      "I1v2", "I2v2", "I3v2"  # Isolated V2 tier
    ], var.frontend_service_plan_sku)
    error_message = "frontend_service_plan_sku must be a valid App Service Plan SKU."
  }
}

variable "backend_service_plan_sku" {
  description = "The SKU name for the Backend App Service Plan"
  type        = string
  default     = "S3"

  validation {
    condition = contains([
      "S1", "S2", "S3",       # Standard tier
      "P1v2", "P2v2", "P3v2", # Premium V2 tier  
      "P1v3", "P2v3", "P3v3", # Premium V3 tier
      "I1v2", "I2v2", "I3v2"  # Isolated V2 tier
    ], var.backend_service_plan_sku)
    error_message = "backend_service_plan_sku must be a valid App Service Plan SKU."
  }
}

variable "worker_service_plan_sku" {
  description = "The SKU name for the Worker App Service Plan (dedicated for transcription processing)"
  type        = string
  default     = "S3"

  validation {
    condition = contains([
      "S1", "S2", "S3",       # Standard tier
      "P1v2", "P2v2", "P3v2", # Premium V2 tier  
      "P1v3", "P2v3", "P3v3", # Premium V3 tier
      "I1v2", "I2v2", "I3v2"  # Isolated V2 tier
    ], var.worker_service_plan_sku)
    error_message = "worker_service_plan_sku must be a valid App Service Plan SKU."
  }
}

# Recording configuration
variable "max_recording_minutes" {
  description = "Maximum recording duration in minutes"
  type        = number
  default     = 55

  validation {
    condition     = var.max_recording_minutes > 0 && var.max_recording_minutes <= 180
    error_message = "max_recording_minutes must be between 1 and 180 minutes."
  }
}