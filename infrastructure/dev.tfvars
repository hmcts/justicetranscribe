environment = "dev"
docker_image_tag = "dev"

# Authentication configuration (always enabled)
auth_client_id = "5087b20c-ae0e-40dd-ad76-55adabfefb92"
auth_tenant_id = "c6874728-71e6-41fe-a9e1-2e8c36776ad8"

backend_docker_image_tag = "dev"

# Service Plan configuration - smaller for dev environment
frontend_service_plan_sku = "S1"  # 1 vCPU, 1.75GB RAM for frontend dev
backend_service_plan_sku = "S2"   # 2 vCPU, 3.5GB RAM for backend dev

# Database configuration - PASSWORD NOW AUTO-GENERATED
# postgres_admin_password = "CHANGE_ME_SECURE_PASSWORD_123!" # REMOVED - now auto-generated

# Optional: Allow specific IP addresses to connect directly to the database
# Uncomment and add your IPs if you need direct database access
# postgres_allowed_ips = ["203.0.113.1", "198.51.100.0"]

# Recording configuration
# max_recording_minutes = 55  # Default: 55 minutes. Uncomment to override.