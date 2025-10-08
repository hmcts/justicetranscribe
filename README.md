[![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)<br>
[![Tests and Coverage](https://github.com/JusticeAIUnit/justicetranscribe/actions/workflows/test-coverage.yml/badge.svg)](https://github.com/JusticeAIUnit/justicetranscribe/actions/workflows/test-coverage.yml)
[![codecov](https://codecov.io/github/justiceaiunit/justicetranscribe/graph/badge.svg?token=DVNAHD4G2O)](https://codecov.io/github/justiceaiunit/justicetranscribe)

# justicetranscribe

A Next.js application deployed to Azure with Terraform

## Author

JusticeAIUnit (sam.lhuillier@justice.gov.uk)

## Local Development

### Quick Start

1. **Copy environment files:**

   ```bash
   cp .env.example .env
   ```

2. **Install dependencies:**

   ```bash
   make install        # Install backend and frontend dependencies
   ```

3. **Start the development environment:**

   ```bash
   # Option 1: Start full stack with Docker Compose
   docker-compose up

   # Option 2: Start database and run migrations
   make database       # Start database and apply migrations
   ```

4. **Access your applications:**
   - **Backend API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs
   - **Database Admin**: http://localhost:8080 (if using Adminer)
   - **Frontend**: http://localhost:3000 (when using full docker-compose)

### Development Workflow

**Installation:**

```bash
make install        # Install backend and frontend dependencies
```

**Backend Development:**

```bash
make backend        # Start backend development server with auto-reload
```

**Frontend Development:**

```bash
make frontend       # Start frontend development server
```

**Database Management:**

```bash
make database       # Start database and run migrations
make db-reset       # Reset database (destroy and recreate)
make db-migrate     # Generate a new database migration
make db-upgrade     # Apply all pending database migrations
```

**Testing:**

```bash
make test           # Run tests (when available)
```

**Full Stack Development:**

```bash
# Start full stack (database + backend + frontend)
docker-compose up

```

**Allowlist Management:**

Helper utilities are available for managing user access allowlists. See [scripts/allowlist/README.md](scripts/allowlist/README.md) for detailed documentation.

### Environment Variables

The backend uses environment variables from `.env` files:

- `DATABASE_CONNECTION_STRING`: PostgreSQL connection string
- `ENVIRONMENT`: Set to "development" for local development
- `AUTH_CLIENT_ID/AUTH_TENANT_ID`: Mock values for local development

See `backend/.env.example` for all available variables.

## Production Setup

### Infrastructure Deployment

Deploy your infrastructure for each environment:

```bash
make setup-dev
make setup-prod
make setup-preprod # optional really
```

### Security Model

All environments (dev, preprod, prod) use **identical security configurations**:

- **Database Access**: Restricted to Azure internal services only
- **Authentication**: Azure AD required for all environments
- **SSL/TLS**: Enforced for all connections
- **Network Security**: No environment has wide-open access

This ensures development and staging environments closely resemble production, following security best practices and reducing deployment surprises.

## Deployment

This project uses GitHub Actions for CI/CD with environment-specific deployments.

### Github Repo:

IMPORTANT: make sure you've named the repo in cruft the same as the github repo name.

### GitHub Secrets Setup

You need to set up the following GitHub secrets. **Important**: Run each infrastructure setup command above and copy the client ID output for each environment:

**Required for all environments:**

- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

**Environment-specific client IDs:**

- `AZURE_CLIENT_ID_DEV` - Copy this from the output of `make setup-dev`
- `AZURE_CLIENT_ID_PROD` - Copy this from the output of `make setup-prod`
- `AZURE_CLIENT_ID_PREPROD` - Copy this from the output of `make setup-preprod`

### Deployment Triggers

The infrastructure will be automatically deployed based on the branch:

- Push to `main` branch → Production environment
- Push to `dev` branch → Development environment
- Push to `preprod` branch → Pre-production environment

### Domains

To setup a justice.gov.uk domain, you need to:

1. Get the azurewebsites.net domain from the Azure Portal (in the frontend app service)
2. Create a CNAME record in [this repo](https://github.com/ministryofjustice/dns) following this [naming convention](https://user-guide.operations-engineering.service.justice.gov.uk/documentation/services/domain-naming-standard.html#domain-naming-standard)
3. Go to 'Add custom domain' in the azure app service portal, create a new domain and select "All other domain services"

## Azure App Service Authentication Troubleshooting (NOT RELEVANT ANYMORE)

If you encounter authentication issues after deploying, here are common problems and solutions:

### HTTP 401 Error After Successful Login

**Symptoms:** You can log in with Microsoft, but then get "HTTP ERROR 401" on your app.

**Common Causes & Solutions:**

#### 1. Missing Redirect URI in Entra App Registration

The most common issue. Your Entra app registration needs the correct callback URL.

**Solution:**

1. Go to [Azure Portal](https://portal.azure.com) → Azure Active Directory → App registrations
2. Find your app registration (Client ID from your `.tfvars` file)
3. Go to **Authentication** → **Platform configurations** → **Add a platform** → **Web**
4. Add redirect URI: `https://[your-app-name].azurewebsites.net/.auth/login/aad/callback`

#### 2. ID Tokens Not Enabled

**Error:** `'id_token' is disabled for this app`

**Solution:**

1. In your Entra app registration, go to **Authentication**
2. Under **Implicit grant and hybrid flows**, check both:
   - ✅ **ID tokens (used for implicit and hybrid flows)** (REQUIRED)
   - ✅ **Access tokens (used for implicit flows)** (RECOMMENDED)

#### 3. User Audience Configuration Mismatch

**Error:** `The request is not valid for the application's 'userAudience' configuration`

**Solution:**

1. In your Entra app registration, go to **Manifest**
2. Find the `signInAudience` property and change it to:
   ```json
   "signInAudience": "AzureADandPersonalMicrosoftAccount"
   ```
3. Save the manifest

### Getting Your App Service URL

To find your exact callback URL for Entra app registration:

1. Run `terraform output auth_callback_url` in the `infrastructure/` directory
2. Or check the Azure Portal → App Services → your app → Overview → URL

### Debugging Authentication Issues

1. **Check App Service logs:**

   - Azure Portal → your App Service → Monitoring → Log stream
   - Try logging in and watch for detailed error messages

2. **Browser Developer Tools:**

   - Open Network tab when logging in
   - Look for failed requests with specific error messages

3. **Verify configuration:**
   - Client ID in `.tfvars` matches Entra app registration
   - Client secret is correct and not expired
   - Tenant ID is correct (`"common"` for multi-tenant or specific tenant ID)
