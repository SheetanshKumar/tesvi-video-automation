SHELL := /usr/bin/env bash

DB_URL          ?= postgres://tesvi:tesvi@localhost:5432/tesvi?sslmode=disable
MIGRATIONS_DIR  := db/migrations

.PHONY: help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[1m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ---------------------------------------------------------------- local db --

.PHONY: db-up
db-up: ## Start local Postgres in Docker
	docker compose up -d postgres

.PHONY: db-down
db-down: ## Stop local Postgres
	docker compose down

.PHONY: db-logs
db-logs: ## Tail Postgres logs
	docker compose logs -f postgres

.PHONY: db-psql
db-psql: ## Open a psql shell against the local DB
	docker compose exec postgres psql -U tesvi -d tesvi

# ---------------------------------------------------------------- migrate --

.PHONY: migrate-up
migrate-up: ## Apply all pending migrations
	migrate -path $(MIGRATIONS_DIR) -database "$(DB_URL)" up

.PHONY: migrate-down
migrate-down: ## Roll back the most recent migration
	migrate -path $(MIGRATIONS_DIR) -database "$(DB_URL)" down 1

.PHONY: migrate-status
migrate-status: ## Show the current migration version
	migrate -path $(MIGRATIONS_DIR) -database "$(DB_URL)" version

.PHONY: migrate-create
migrate-create: ## Create a new migration pair. Usage: make migrate-create name=add_users_table
	@if [ -z "$(name)" ]; then echo "usage: make migrate-create name=<snake_case_name>"; exit 1; fi
	migrate create -ext sql -dir $(MIGRATIONS_DIR) -seq $(name)

# ---------------------------------------------------------------- go services --

GO_SERVICES := api source-ingestor render-orchestrator publisher

.PHONY: go-build
go-build: ## Build every Go service
	@for svc in $(GO_SERVICES); do \
	    echo "==> services/$$svc"; \
	    (cd services/$$svc && go build ./...) || exit 1; \
	done

.PHONY: go-test
go-test: ## Test every Go service
	@for svc in $(GO_SERVICES); do \
	    echo "==> services/$$svc"; \
	    (cd services/$$svc && go test ./...) || exit 1; \
	done

.PHONY: go-tidy
go-tidy: ## Run `go mod tidy` in every Go module
	@for svc in $(GO_SERVICES); do \
	    echo "==> services/$$svc"; \
	    (cd services/$$svc && go mod tidy) || exit 1; \
	done

# ---------------------------------------------------------- python services --

.PHONY: py-install
py-install: ## Install the extractor (with dev extras) into the current environment
	python -m pip install -e 'services/extractor[dev]'

.PHONY: py-test
py-test: ## Run extractor tests
	python -m pytest services/extractor

# -------------------------------------------------------------- ts services --

TS_SERVICES := renderer reviewer-ui

.PHONY: ts-install
ts-install: ## `npm install` in every TS service
	@for svc in $(TS_SERVICES); do \
	    echo "==> services/$$svc"; \
	    (cd services/$$svc && npm install --no-audit --no-fund) || exit 1; \
	done

.PHONY: ts-typecheck
ts-typecheck: ## Typecheck every TS service
	@for svc in $(TS_SERVICES); do \
	    echo "==> services/$$svc"; \
	    (cd services/$$svc && npm run typecheck) || exit 1; \
	done

.PHONY: ts-build
ts-build: ## Build every TS service (currently only renderer produces artefacts here)
	@cd services/renderer && npm run build

# ------------------------------------------------------------------- meta --

.PHONY: build
build: go-build ts-build ## Build all services (Go + TS)

.PHONY: test
test: go-test py-test ## Run all fast test suites
