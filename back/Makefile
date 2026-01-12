.PHONY: up down build logs shell db-shell n8n-logs restart clean

# ============================================
# Docker Compose Commands
# ============================================

## Start all services
up:
	docker-compose up -d

## Start with build
up-build:
	docker-compose up --build

## Stop all services
down:
	docker-compose down

## Stop and remove volumes (clean slate)
clean:
	docker-compose down -v

## Rebuild specific service
build:
	docker-compose build backend

## View logs for all services
logs:
	docker-compose logs -f

## View backend logs only
logs-backend:
	docker-compose logs -f backend

## View n8n logs only
logs-n8n:
	docker-compose logs -f n8n

## Restart backend
restart:
	docker-compose restart backend

## Restart all
restart-all:
	docker-compose restart

# ============================================
# Shell Access
# ============================================

## Access backend container shell
shell:
	docker-compose exec backend bash

## Access database shell
db-shell:
	docker-compose exec db psql -U postgres -d retry_db

## Access n8n container shell
n8n-shell:
	docker-compose exec n8n sh

# ============================================
# Development Commands
# ============================================

## Start with pgAdmin for debugging
debug:
	docker-compose --profile debug up -d

## Run database migrations (if using alembic)
migrate:
	docker-compose exec backend alembic upgrade head

## Create new migration
migration:
	docker-compose exec backend alembic revision --autogenerate -m "$(name)"

# ============================================
# Testing & Demo
# ============================================

## Run tests
test:
	docker-compose exec backend pytest

## Test API health
health:
	curl -s http://localhost:8000/health | python -m json.tool

## Test simulate failure - Insufficient Funds
simulate:
	curl -X POST http://localhost:8000/api/v1/simulate/failure \
		-H "Content-Type: application/json" \
		-d '{"merchant_id": "466fd34b-96a1-4635-9b2c-dedd2645291f", "amount_cents": 10000, "failure_type": "insufficient_funds"}' \
		| python -m json.tool

## Test simulate failure - Network Timeout (high success rate)
simulate-network:
	curl -X POST http://localhost:8000/api/v1/simulate/failure \
		-H "Content-Type: application/json" \
		-d '{"merchant_id": "11111111-1111-1111-1111-111111111111", "amount_cents": 25000, "failure_type": "network_timeout"}' \
		| python -m json.tool

## Test simulate failure - Card Declined
simulate-declined:
	curl -X POST http://localhost:8000/api/v1/simulate/failure \
		-H "Content-Type: application/json" \
		-d '{"merchant_id": "11111111-1111-1111-1111-111111111111", "amount_cents": 5000, "failure_type": "card_declined"}' \
		| python -m json.tool

## Test simulate failure - Fraud (non-retriable)
simulate-fraud:
	curl -X POST http://localhost:8000/api/v1/simulate/failure \
		-H "Content-Type: application/json" \
		-d '{"merchant_id": "11111111-1111-1111-1111-111111111111", "amount_cents": 100000, "failure_type": "fraud"}' \
		| python -m json.tool

## Get retry config for demo merchant
get-config:
	curl -s http://localhost:8000/api/v1/retry-config/11111111-1111-1111-1111-111111111111 | python -m json.tool

## Preview retry settings (what would happen)
preview:
	curl -s http://localhost:8000/api/v1/retry-config/11111111-1111-1111-1111-111111111111/preview | python -m json.tool

## Get stats for demo merchant
stats:
	curl -s http://localhost:8000/api/v1/simulate/stats/11111111-1111-1111-1111-111111111111 | python -m json.tool

## List all payments
payments:
	curl -s "http://localhost:8000/api/v1/payments/?merchant_id=11111111-1111-1111-1111-111111111111" | python -m json.tool

## Disable retry for demo merchant
disable-retry:
	curl -X PUT http://localhost:8000/api/v1/retry-config/11111111-1111-1111-1111-111111111111 \
		-H "Content-Type: application/json" \
		-d '{"retry_enabled": false}' \
		| python -m json.tool

## Enable retry for demo merchant
enable-retry:
	curl -X PUT http://localhost:8000/api/v1/retry-config/11111111-1111-1111-1111-111111111111 \
		-H "Content-Type: application/json" \
		-d '{"retry_enabled": true}' \
		| python -m json.tool

## Test n8n webhook directly
test-n8n:
	curl -X POST http://localhost:5678/webhook/payment-failed \
		-H "Content-Type: application/json" \
		-d '{"payment_id": "test-direct-123", "merchant_id": "11111111-1111-1111-1111-111111111111", "amount_cents": 15000, "failure_type": "network_timeout", "attempt_number": 1, "delay_minutes": 1, "max_attempts": 3, "callback_url": "http://backend:8000/api/v1/webhooks/retry-result"}' \
		| python -m json.tool

# ============================================
# Info
# ============================================

## Show service URLs
urls:
	@echo "=========================================="
	@echo "Service URLs:"
	@echo "=========================================="
	@echo "Backend API:  http://localhost:8000"
	@echo "API Docs:     http://localhost:8000/docs"
	@echo "n8n:          http://localhost:5678"
	@echo "pgAdmin:      http://localhost:5050 (debug mode)"
	@echo "=========================================="
	@echo ""
	@echo "n8n Credentials:"
	@echo "  User: admin"
	@echo "  Pass: admin123"
	@echo ""
	@echo "pgAdmin Credentials:"
	@echo "  Email: admin@admin.com"
	@echo "  Pass: admin"
	@echo "=========================================="

## Show help
help:
	@echo "Available commands:"
	@echo ""
	@echo "Docker:"
	@echo "  make up          - Start all services"
	@echo "  make up-build    - Start with rebuild"
	@echo "  make down        - Stop all services"
	@echo "  make clean       - Stop and remove volumes"
	@echo "  make logs        - View all logs"
	@echo ""
	@echo "Development:"
	@echo "  make shell       - Access backend shell"
	@echo "  make db-shell    - Access database shell"
	@echo "  make urls        - Show service URLs"
	@echo ""
	@echo "Demo Commands:"
	@echo "  make health          - Test API health"
	@echo "  make simulate        - Simulate insufficient_funds failure"
	@echo "  make simulate-network- Simulate network_timeout (high success)"
	@echo "  make simulate-fraud  - Simulate fraud (non-retriable)"
	@echo "  make get-config      - Get merchant retry config"
	@echo "  make preview         - Preview retry settings impact"
	@echo "  make stats           - Get retry statistics"
	@echo "  make payments        - List all payments"
	@echo "  make enable-retry    - Enable retry for demo merchant"
	@echo "  make disable-retry   - Disable retry for demo merchant"
	@echo "  make test-n8n        - Test n8n webhook directly"
