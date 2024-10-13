APP_NAME := `sed -n 's/^ *name.*=.*"\([^"]*\)".*/\1/p' pyproject.toml`
APP_VERSION := `sed -n 's/^ *version.*=.*"\([^"]*\)".*/\1/p' pyproject.toml`

# Makefile help

.PHONY: help
help: header usage options ## Print help

.PHONY: header
header:
	@echo -ne "\033[34mEnvironment\033[0m"
	@echo ""
	@echo -ne "\033[34m---------------------------------------------------------------\033[0m"
	@echo ""
	@echo -n -e "\033[33mAPP_NAME: \033[0m"
	@echo -e "\033[35m$(APP_NAME)\033[0m"
	@echo -n -e "\033[33mAPP_VERSION: \033[0m"
	@echo -e "\033[35m$(APP_VERSION)\033[0m"
	@echo ""

.PHONY: usage
usage:
	@echo -ne "\033[034mUsage\033[0m"
	@echo ""
	@echo -ne "\033[34m---------------------------------------------------------------\033[0m"
	@echo ""
	@echo -n -e "\033[37mmake [options] \033[0m"
	@echo ""
	@echo ""

.PHONY: options
options:
	@echo -ne "\033[34mOptions\033[0m"
	@echo ""
	@echo -ne "\033[34m---------------------------------------------------------------\033[0m"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}' | sort

# Makefile commands

.PHONY: run
run:
	@make start-worker &
	@make start

start-worker: ## Start background workers
	$(eval include .env)
	$(eval export $(sh sed 's/=.*//' .env))
	
	poetry run dramatiq worker

.PHONY: start
start: ## Start the server
	$(eval include .env)
	$(eval export $(sh sed 's/=.*//' .env))

	poetry run python main.py

.PHONY: cli
cli: ## Start the CLI
	$(eval include .env)
	$(eval export $(shell sed 's/=.*//' .env))
	poetry run python cli.py $(filter-out $@,$(MAKECMDGOALS))

%:
	@true

# Database commands

.PHONY: migrate
migrate: ## Run the migrations
	$(eval include .env)
	$(eval export $(sh sed 's/=.*//' .env))

	poetry run alembic upgrade head

.PHONY: rollback
rollback: ## Rollback the migrations
	$(eval include .env)
	$(eval export $(sh sed 's/=.*//' .env))

	poetry run alembic downgrade -1

.PHONY: generate-migration
generate-migration: ## Generate a new migration
	$(eval include .env)
	$(eval export $(sh sed 's/=.*//' .env))

	@echo -ne "\033[33mEnter migration message: \033[0m"
	@read -r message; \
	poetry run alembic revision --autogenerate -m "$$message"
	# @make lint migration

# Code quality commands

.PHONY: check
check: ## Check and lint the code
	@make check-format
	@make lint

.PHONY: check-format
check-format: ## Check format
	-poetry run black ./ --check
	-poetry run ruff check --select I --select W --select E

.PHONY: lint
lint: ## Lint the code
	poetry run black ./
	poetry run ruff check --fix --select I --select W --select E

