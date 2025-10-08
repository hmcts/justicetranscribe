# Add this near the top of your Makefile
.PHONY: setup-dev setup-prod setup-preprod install backend frontend database db-up db-down db-reset db-migrate db-upgrade test allowlist-dev allowlist-prod allowlist-both allowlist-update-dev allowlist-update-prod allowlist-merge-dev allowlist-merge-prod allowlist-upload-dev allowlist-upload-prod
# Complete Dev Environment Setup
setup-dev:
	@echo "🚀 Setting up DEV environment end-to-end..."
	@echo "📦 Step 1/2: Initializing Terraform..."
	terraform -chdir=infrastructure init -reconfigure -backend-config="key=dev.terraform.tfstate"
	@echo "⚡ Step 2/2: Applying changes (will show plan first)..."
	terraform -chdir=infrastructure apply -var-file="dev.tfvars"
	@echo "✅ DEV environment setup complete!"
# Complete Prod Environment Setup  
setup-prod:
	@echo "🚀 Setting up PROD environment end-to-end..."
	@echo "⚠️  WARNING: You are setting up PRODUCTION infrastructure!"
	@read -p "Continue with PROD setup? [y/N]: " confirm && [ "$$confirm" = "y" ]
	@echo "📦 Step 1/2: Initializing Terraform..."
	terraform -chdir=infrastructure init -reconfigure -backend-config="key=prod.terraform.tfstate"
	@echo "⚡ Step 2/2: Applying changes (will show plan first)..."
	terraform -chdir=infrastructure apply -var-file="prod.tfvars"
	@echo "✅ PROD environment setup complete!"
# Complete Preprod Environment Setup
setup-preprod:
	@echo "🚀 Setting up PREPROD environment end-to-end..."
	@echo "📦 Step 1/2: Initializing Terraform..."
	terraform -chdir=infrastructure init -reconfigure -backend-config="key=preprod.terraform.tfstate"
	@echo "⚡ Step 2/2: Applying changes (will show plan first)..."
	terraform -chdir=infrastructure apply -var-file="preprod.tfvars"
	@echo "✅ PREPROD environment setup complete!"

install: ## Install backend dependencies
	cd backend && uv sync --group fastapi --group dev
	cd frontend && npm install
backend: ## Run development server
	@if [ -f .env ]; then \
		echo "📄 Loading environment variables from .env file..."; \
		cd backend && ENVIRONMENT=local uv run --env-file ../.env uvicorn main:app --reload --host 0.0.0.0 --port 8000; \
	else \
		echo "⚠️  No .env file found. Make sure to create one from .env.example"; \
		cd backend && ENVIRONMENT=local uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000; \
	fi
frontend: ## Run development server
	cd frontend && NEXT_PUBLIC_API_URL=http://localhost:8000 INTERNAL_API_BASE=http://localhost:8000 ENVIRONMENT=local NODE_ENV=development npm run dev
database:
	docker compose up database
	make db-upgrade
db-reset: ## Reset database (destroy and recreate)
	docker compose down -v
	docker compose up -d database
	sleep 5
	$(MAKE) db-upgrade
db-migrate: ## Generate a new database migration
	cd backend && uv run alembic revision --autogenerate
db-upgrade: ## Apply all pending database migrations
	cd backend && uv run alembic upgrade head
test: ## Run tests (when available)
	cd backend && uv run pytest
# JusticeAIUnit Allowlist Management
# Update development allowlist
allowlist-dev:
	cd scripts/allowlist && python munge_allowlist.py --env dev
# Update production allowlist  
allowlist-prod:
	cd scripts/allowlist && python munge_allowlist.py --env prod
# Update both allowlists
allowlist-both:
	cd scripts/allowlist && python munge_allowlist.py --env both
# Create a timestamped allowlist update CSV from clipboard input
# Usage: make allowlist-update-dev [PROVIDER="region-name"]
# Usage: make allowlist-update-prod [PROVIDER="region-name"]
# PROVIDER is optional - if not specified, uses "unknown" for rows without provider
allowlist-update-dev:
	@if [ -z "$(PROVIDER)" ]; then \
		cd scripts/allowlist && python create_allowlist_update.py --env dev; \
	else \
		cd scripts/allowlist && python create_allowlist_update.py --env dev --provider "$(PROVIDER)"; \
	fi
allowlist-update-prod:
	@if [ -z "$(PROVIDER)" ]; then \
		cd scripts/allowlist && python create_allowlist_update.py --env prod; \
	else \
		cd scripts/allowlist && python create_allowlist_update.py --env prod --provider "$(PROVIDER)"; \
	fi
# Merge a local allowlist file with Azure and upload
# Usage: make allowlist-merge-dev FILE=data/dev-allowlist-update-2025-10-08_12-06-24.csv
# Usage: make allowlist-merge-prod FILE=data/prod-allowlist-update-2025-10-08_12-06-24.csv
allowlist-merge-dev:
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Error: FILE is required"; \
		echo "Usage: make allowlist-merge-dev FILE=data/dev-allowlist-update-YYYY-MM-DD_HH-MM-SS.csv"; \
		exit 1; \
	fi
	@if [ ! -f "$(FILE)" ]; then \
		echo "❌ Error: File not found: $(FILE)"; \
		exit 1; \
	fi
	cd scripts/allowlist && python merge_and_upload_allowlist.py --env dev --file ../../$(FILE)
allowlist-merge-prod:
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Error: FILE is required"; \
		echo "Usage: make allowlist-merge-prod FILE=data/prod-allowlist-update-YYYY-MM-DD_HH-MM-SS.csv"; \
		exit 1; \
	fi
	@if [ ! -f "$(FILE)" ]; then \
		echo "❌ Error: File not found: $(FILE)"; \
		exit 1; \
	fi
	@echo "⚠️  WARNING: You are updating PRODUCTION allowlist!"
	@read -p "Continue? [y/N]: " confirm && [ "$$confirm" = "y" ]
	cd scripts/allowlist && python merge_and_upload_allowlist.py --env prod --file ../../$(FILE)
# One-step: Create timestamped CSV from stdin and upload to Azure
# Usage: make allowlist-upload-dev [PROVIDER="region-name"]
# Usage: make allowlist-upload-prod [PROVIDER="region-name"]
allowlist-upload-dev:
	@echo "📋 Step 1/2: Creating timestamped allowlist CSV..."
	@if [ -z "$(PROVIDER)" ]; then \
		CREATED_FILE=$$(cd scripts/allowlist && python create_allowlist_update.py --env dev 2>&1 | grep "File:" | sed 's/.*File: //'); \
	else \
		CREATED_FILE=$$(cd scripts/allowlist && python create_allowlist_update.py --env dev --provider "$(PROVIDER)" 2>&1 | grep "File:" | sed 's/.*File: //'); \
	fi; \
	if [ -z "$$CREATED_FILE" ]; then \
		echo "❌ Failed to create allowlist file"; \
		exit 1; \
	fi; \
	echo ""; \
	echo "📤 Step 2/2: Merging and uploading to Azure..."; \
	cd scripts/allowlist && python merge_and_upload_allowlist.py --env dev --file "$$CREATED_FILE"
allowlist-upload-prod:
	@echo "⚠️  WARNING: You are updating PRODUCTION allowlist!"
	@read -p "Continue? [y/N]: " confirm && [ "$$confirm" = "y" ]
	@echo "📋 Step 1/2: Creating timestamped allowlist CSV..."
	@if [ -z "$(PROVIDER)" ]; then \
		CREATED_FILE=$$(cd scripts/allowlist && python create_allowlist_update.py --env prod 2>&1 | grep "File:" | sed 's/.*File: //'); \
	else \
		CREATED_FILE=$$(cd scripts/allowlist && python create_allowlist_update.py --env prod --provider "$(PROVIDER)" 2>&1 | grep "File:" | sed 's/.*File: //'); \
	fi; \
	if [ -z "$$CREATED_FILE" ]; then \
		echo "❌ Failed to create allowlist file"; \
		exit 1; \
	fi; \
	echo ""; \
	echo "📤 Step 2/2: Merging and uploading to Azure..."; \
	cd scripts/allowlist && python merge_and_upload_allowlist.py --env prod --file "$$CREATED_FILE"
