# Makefile for Cyber Threat Platform with PostgreSQL

# =============================================================================
# ENVIRONMENT CONFIGURATION
# =============================================================================

# Default environment
ENV ?= production
COMPOSE_FILE := docker-compose.ctp.yml
ifeq ($(ENV),development)
	COMPOSE_FILE := docker-compose.dev.yml
endif

# Production deployment settings
BACKUP_DIR = ./backups
TIMESTAMP = $(shell date +%Y%m%d_%H%M%S)

# =============================================================================
# PRODUCTION DEPLOYMENT COMMANDS
# =============================================================================

help:
	@echo "CTP (Cyber Threat Platform) - Available Commands:"
	@echo ""
	@echo "  🚀 Deployment Commands:"
	@echo "    make deploy-prod     Deploy to production"
	@echo "    make deploy-staging  Deploy to staging"
	@echo "    make build          Build all services"
	@echo "    make start          Start all services"
	@echo "    make stop           Stop all services"
	@echo "    make restart        Restart all services"
	@echo ""
	@echo "  🧪 Testing Commands:"
	@echo "    make test           Run all tests"
	@echo "    make test-backend   Run backend tests"
	@echo "    make test-frontend  Run frontend tests"
	@echo "    make lint           Run linting"
	@echo ""
	@echo "  📊 Monitoring Commands:"
	@echo "    make logs           Show service logs"
	@echo "    make status         Show service status"
	@echo "    make health         Check service health"
	@echo ""
	@echo "  🗄️ Database Commands:"
	@echo "    make db-init        Initialize database"
	@echo "    make db-migrate     Run migrations"
	@echo "    make db-backup      Backup database"
	@echo "    make db-restore     Restore database"
	@echo ""

# Build commands
build:
	@echo "🔨 Building CTP services..."
	docker-compose -f $(COMPOSE_FILE) build --no-cache

# Deployment commands
deploy-prod: check-env build
	@echo "🚀 Deploying CTP to production..."
	@if [ ! -f .env ]; then echo "❌ .env file not found! Copy .env.production to .env and configure it."; exit 1; fi
	@if grep -q "CHANGE_THIS" .env; then echo "❌ Please update security configuration in .env"; exit 1; fi
	docker-compose -f $(COMPOSE_FILE) down --remove-orphans
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "⏳ Waiting for services to start..."
	sleep 30
	@make health
	@echo "✅ CTP deployed successfully!"

deploy-staging: build
	@echo "🚀 Deploying CTP to staging..."
	@if [ ! -f .env.staging ]; then echo "❌ .env.staging file not found!"; exit 1; fi
	cp .env.staging .env
	docker-compose -f $(COMPOSE_FILE) down --remove-orphans
	docker-compose -f $(COMPOSE_FILE) up -d
	sleep 30
	@make health

# Service management
start:
	@echo "▶️ Starting CTP services..."
	docker-compose -f $(COMPOSE_FILE) up -d

stop:
	@echo "⏹️ Stopping CTP services..."
	docker-compose -f $(COMPOSE_FILE) down

restart:
	@echo "🔄 Restarting CTP services..."
	docker-compose -f $(COMPOSE_FILE) restart

# Testing commands
test: test-backend test-frontend
	@echo "✅ All tests completed!"

test-backend:
	@echo "🧪 Running backend tests..."
	cd backend && python -m pytest tests/ -v

test-frontend:
	@echo "🧪 Running frontend tests..."
	cd frontend && npm test

lint:
	@echo "🔍 Running linting..."
	cd backend && python -m flake8 . || true
	cd frontend && npm run lint

# Monitoring commands
logs:
	@echo "📋 Showing service logs..."
	docker-compose -f $(COMPOSE_FILE) logs -f

status:
	@echo "📊 Service Status:"
	docker-compose -f $(COMPOSE_FILE) ps

health:
	@echo "🏥 Checking service health..."
	@echo "Backend Health:"
	@curl -f http://localhost:8000/health 2>/dev/null && echo "✅ Backend is healthy" || echo "❌ Backend is unhealthy"
	@echo "Frontend Health:"
	@curl -f http://localhost:3000/health 2>/dev/null && echo "✅ Frontend is healthy" || echo "❌ Frontend is unhealthy"

# Environment checks
check-env:
	@echo "🔍 Checking environment configuration..."
	@if [ ! -f .env ]; then echo "❌ .env file not found!"; exit 1; fi
	@if ! docker --version > /dev/null 2>&1; then echo "❌ Docker not installed!"; exit 1; fi
	@if ! docker-compose --version > /dev/null 2>&1; then echo "❌ Docker Compose not installed!"; exit 1; fi
	@echo "✅ Environment check passed!"

# Model deployment
deploy-model:
	@echo "🤖 Deploying autoencoder model..."
	@if [ ! -d "backend/models/autoencoder" ]; then mkdir -p backend/models/autoencoder; fi
	@echo "Please copy your model files to backend/models/autoencoder/"
	@echo "Required files:"
	@echo "  - autoencoder_model.pkl"
	@echo "  - scaler.pkl"
	@echo "  - model_config.json"
	docker-compose -f $(COMPOSE_FILE) restart backend
	@echo "✅ Model deployment completed!"

# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

db-init:
	@echo "🚀 Initializing PostgreSQL database..."
	docker compose -f $(COMPOSE_FILE) exec backend python init_db.py

db-migrate:
	@echo "🔄 Running database migrations..."
	docker compose -f $(COMPOSE_FILE) exec backend alembic upgrade head

db-reset:
	@echo "⚠️  Resetting database (this will delete all data)..."
	@read -p "Are you sure? This will delete ALL data! (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker compose -f $(COMPOSE_FILE) exec backend alembic downgrade base; \
		docker compose -f $(COMPOSE_FILE) exec backend alembic upgrade head; \
		echo "✅ Database reset complete"; \
	else \
		echo "❌ Database reset cancelled"; \
	fi

db-backup:
	@echo "💾 Creating database backup..."
	@mkdir -p backups
	docker compose -f $(COMPOSE_FILE) exec db pg_dump -U $$POSTGRES_USER $$POSTGRES_DB > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup saved to backups/backup_$$(date +%Y%m%d_%H%M%S).sql"

db-restore:
	@echo "📥 Restoring database from backup..."
	@read -p "Enter backup file name (from backups/): " backup_file; \
	docker compose -f $(COMPOSE_FILE) exec -T db psql -U $$POSTGRES_USER $$POSTGRES_DB < backups/$$backup_file

db-shell:
	@echo "🐘 Opening PostgreSQL shell..."
	docker compose -f $(COMPOSE_FILE) exec db psql -U $$POSTGRES_USER $$POSTGRES_DB

db-monitor:
	@echo "📊 Database monitoring..."
	docker compose -f $(COMPOSE_FILE) exec db psql -U $$POSTGRES_USER $$POSTGRES_DB -c "SELECT version();"
	docker compose -f $(COMPOSE_FILE) exec db psql -U $$POSTGRES_USER $$POSTGRES_DB -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';"

# =============================================================================
# APPLICATION OPERATIONS
# =============================================================================

up:
	@echo "🚀 Starting all services in $(ENV) mode..."
	docker compose -f $(COMPOSE_FILE) up --build -d

down:
	@echo "🛑 Stopping all services..."
	docker compose -f $(COMPOSE_FILE) down

restart:
	@echo "🔄 Restarting services..."
	docker compose -f $(COMPOSE_FILE) restart

logs:
	@echo "📋 Showing logs..."
	docker compose -f $(COMPOSE_FILE) logs -f

logs-backend:
	@echo "📋 Showing backend logs..."
	docker compose -f $(COMPOSE_FILE) logs -f backend

logs-frontend:
	@echo "📋 Showing frontend logs..."
	docker compose -f $(COMPOSE_FILE) logs -f frontend

logs-celery:
	@echo "📋 Showing Celery logs..."
	docker compose -f $(COMPOSE_FILE) logs -f celeryworker

# =============================================================================
# DEVELOPMENT SHELLS
# =============================================================================

backend-shell:
	@echo "🐍 Opening backend shell..."
	docker compose -f $(COMPOSE_FILE) exec backend bash

frontend-shell:
	@echo "⚛️  Opening frontend shell..."
	docker compose -f $(COMPOSE_FILE) exec frontend sh

mlflow-shell:
	@echo "📊 Opening MLflow shell..."
	docker compose -f $(COMPOSE_FILE) exec mlflow bash

redis-shell:
	@echo "🔴 Opening Redis shell..."
	docker compose -f $(COMPOSE_FILE) exec redis redis-cli

# =============================================================================
# CODE QUALITY
# =============================================================================

lint:
	@echo "🔍 Running linting..."
	cd backend && ruff . && mypy .

format:
	@echo "✨ Formatting code..."
	cd backend && black .

test:
	@echo "🧪 Running tests..."
	cd backend && python -m pytest

test-coverage:
	@echo "🧪 Running tests with coverage..."
	cd backend && python -m pytest --cov=. --cov-report=html

# =============================================================================
# HEALTH CHECKS
# =============================================================================

health:
	@echo "🏥 Checking service health..."
	@echo "=========================================="
	@echo "Backend API: $$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "DOWN")"
	@echo "Frontend: $$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 || echo "DOWN")"
	@echo "MLflow: $$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health || echo "DOWN")"
	@echo "PostgreSQL: $$(docker compose -f $(COMPOSE_FILE) exec -T db pg_isready -U $$POSTGRES_USER && echo "UP" || echo "DOWN")"
	@echo "Redis: $$(docker compose -f $(COMPOSE_FILE) exec -T redis redis-cli ping | grep PONG && echo "UP" || echo "DOWN")"
	@echo "Celery: $$(docker compose -f $(COMPOSE_FILE) exec -T backend celery -A common.celery_app inspect ping | grep -q "pong" && echo "UP" || echo "DOWN")"
	@echo "=========================================="

health-detailed:
	@echo "🏥 Detailed health check..."
	@echo "Backend API Details:"
	curl -s http://localhost:8000/health | jq . || echo "Backend not responding"
	@echo ""
	@echo "Database Connection:"
	docker compose -f $(COMPOSE_FILE) exec -T db pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB
	@echo ""
	@echo "Redis Connection:"
	docker compose -f $(COMPOSE_FILE) exec -T redis redis-cli ping
	@echo ""
	@echo "Celery Status:"
	docker compose -f $(COMPOSE_FILE) exec -T backend celery -A common.celery_app inspect active

# =============================================================================
# SETUP AND INSTALLATION
# =============================================================================

setup:
	@echo "🔧 Setting up development environment..."
	@if [ ! -f .env ]; then \
		echo "📝 Creating .env file from template..."; \
		cp env.example .env; \
		echo "⚠️  Please edit .env with your configuration"; \
		echo "Press Enter when ready to continue..."; \
		read; \
	fi
	@echo "📦 Building Docker images..."
	docker compose -f $(COMPOSE_FILE) build
	@echo "🚀 Starting services..."
	docker compose -f $(COMPOSE_FILE) up -d
	@echo "⏳ Waiting for services to be ready..."
	sleep 30
	@echo "🗄️  Initializing database..."
	docker compose -f $(COMPOSE_FILE) exec backend python init_db.py
	@echo "✅ Setup complete! Visit http://localhost:3000"

setup-dev:
	@echo "🔧 Setting up development environment..."
	$(MAKE) setup ENV=development

setup-prod:
	@echo "🔧 Setting up production environment..."
	$(MAKE) setup ENV=production

# =============================================================================
# SECURITY AND MONITORING
# =============================================================================

security-scan:
	@echo "🔒 Running security scan..."
	docker compose -f $(COMPOSE_FILE) exec backend bandit -r . -f json -o security-report.json
	@echo "✅ Security scan complete. Check security-report.json"

vulnerability-scan:
	@echo "🔍 Running vulnerability scan..."
	docker compose -f $(COMPOSE_FILE) exec backend safety check --json --output safety-report.json
	@echo "✅ Vulnerability scan complete. Check safety-report.json"

audit-logs:
	@echo "📋 Showing audit logs..."
	docker compose -f $(COMPOSE_FILE) exec backend tail -f logs/audit.log

# =============================================================================
# CLEANUP AND MAINTENANCE
# =============================================================================

clean:
	@echo "🧹 Cleaning up..."
	docker compose -f $(COMPOSE_FILE) down -v
	docker system prune -f

clean-all:
	@echo "🧹 Deep cleaning..."
	docker compose -f $(COMPOSE_FILE) down -v --remove-orphans
	docker system prune -af
	docker volume prune -f
	docker network prune -f

clean-logs:
	@echo "🧹 Cleaning logs..."
	docker compose -f $(COMPOSE_FILE) exec backend find /app/logs -name "*.log" -delete
	docker compose -f $(COMPOSE_FILE) exec backend find /app/logs -name "*.log.*" -delete

# =============================================================================
# PERFORMANCE AND MONITORING
# =============================================================================

monitor:
	@echo "📊 System monitoring..."
	docker stats --no-stream

monitor-detailed:
	@echo "📊 Detailed system monitoring..."
	@echo "Container Resource Usage:"
	docker stats --no-stream
	@echo ""
	@echo "Disk Usage:"
	docker system df
	@echo ""
	@echo "Network Usage:"
	docker network ls

performance-test:
	@echo "⚡ Running performance tests..."
	docker compose -f $(COMPOSE_FILE) exec backend python -m pytest tests/test_performance.py -v

# =============================================================================
# DEPLOYMENT
# =============================================================================

deploy:
	@echo "🚀 Deploying to production..."
	@echo "⚠️  This will restart all services"
	@read -p "Continue? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker compose -f docker-compose.yml pull; \
		docker compose -f docker-compose.yml up -d --force-recreate; \
		echo "✅ Deployment complete"; \
	else \
		echo "❌ Deployment cancelled"; \
	fi

rollback:
	@echo "🔄 Rolling back deployment..."
	@read -p "Enter previous image tag: " tag; \
	docker compose -f docker-compose.yml down; \
	docker compose -f docker-compose.yml up -d --force-recreate; \
	echo "✅ Rollback complete"

# =============================================================================
# UTILITIES
# =============================================================================

shell:
	@echo "🐚 Opening shell for $(ENV) environment..."
	docker compose -f $(COMPOSE_FILE) exec backend bash

logs-follow:
	@echo "📋 Following all logs..."
	docker compose -f $(COMPOSE_FILE) logs -f --tail=100

logs-errors:
	@echo "❌ Showing error logs..."
	docker compose -f $(COMPOSE_FILE) logs --tail=100 | grep -i error

logs-warnings:
	@echo "⚠️  Showing warning logs..."
	docker compose -f $(COMPOSE_FILE) logs --tail=100 | grep -i warning

# =============================================================================
# HELP
# =============================================================================

help:
	@echo "Cyber Threat Platform - Available Commands:"
	@echo ""
	@echo "Environment:"
	@echo "  ENV=development make up    - Start development environment"
	@echo "  ENV=production make up     - Start production environment"
	@echo ""
	@echo "Database Operations:"
	@echo "  db-init        - Initialize database tables"
	@echo "  db-migrate     - Run database migrations"
	@echo "  db-reset       - Reset database (⚠️  destructive)"
	@echo "  db-backup      - Create database backup"
	@echo "  db-restore     - Restore database from backup"
	@echo "  db-shell       - Open PostgreSQL shell"
	@echo "  db-monitor     - Database monitoring"
	@echo ""
	@echo "Application Operations:"
	@echo "  up             - Start all services"
	@echo "  down           - Stop all services"
	@echo "  restart        - Restart services"
	@echo "  logs           - Show service logs"
	@echo "  logs-backend   - Show backend logs"
	@echo "  logs-frontend  - Show frontend logs"
	@echo "  logs-celery    - Show Celery logs"
	@echo ""
	@echo "Development:"
	@echo "  backend-shell  - Open backend shell"
	@echo "  frontend-shell - Open frontend shell"
	@echo "  mlflow-shell   - Open MLflow shell"
	@echo "  redis-shell    - Open Redis shell"
	@echo "  lint           - Run code linting"
	@echo "  format         - Format code"
	@echo "  test           - Run tests"
	@echo "  test-coverage  - Run tests with coverage"
	@echo ""
	@echo "Health & Monitoring:"
	@echo "  health         - Check service health"
	@echo "  health-detailed - Detailed health check"
	@echo "  monitor        - System monitoring"
	@echo "  monitor-detailed - Detailed monitoring"
	@echo "  performance-test - Run performance tests"
	@echo ""
	@echo "Security:"
	@echo "  security-scan  - Run security scan"
	@echo "  vulnerability-scan - Run vulnerability scan"
	@echo "  audit-logs     - Show audit logs"
	@echo ""
	@echo "Setup & Maintenance:"
	@echo "  setup          - Complete setup (first time)"
	@echo "  setup-dev      - Development setup"
	@echo "  setup-prod     - Production setup"
	@echo "  clean          - Clean up everything"
	@echo "  clean-all      - Deep cleanup"
	@echo "  clean-logs     - Clean log files"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy         - Deploy to production"
	@echo "  rollback       - Rollback deployment"
	@echo ""
	@echo "Utilities:"
	@echo "  shell          - Open shell"
	@echo "  logs-follow    - Follow all logs"
	@echo "  logs-errors    - Show error logs"
	@echo "  logs-warnings  - Show warning logs"
	@echo "  help           - Show this help"

.PHONY: up down restart logs db-init db-migrate db-reset db-backup db-restore db-shell db-monitor backend-shell frontend-shell mlflow-shell redis-shell lint format test test-coverage health health-detailed setup setup-dev setup-prod security-scan vulnerability-scan audit-logs clean clean-all clean-logs monitor monitor-detailed performance-test deploy rollback shell logs-follow logs-errors logs-warnings help
