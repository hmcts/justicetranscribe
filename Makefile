# Add this near the top of your Makefile
.PHONY: setup-dev setup-prod setup-preprod install backend frontend database db-up db-down db-reset db-migrate db-upgrade test allowlist-dev allowlist-prod allowlist-both
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
	cd backend && ENVIRONMENT=local uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
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
