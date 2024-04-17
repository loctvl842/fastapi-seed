APP_NAME := `sed -n 's/^ *name.*=.*"\([^"]*\)".*/\1/p' pyproject.toml`
APP_VERSION := `sed -n 's/^ *version.*=.*"\([^"]*\)".*/\1/p' pyproject.toml`

# Makefile help

.PHONY: help
help: header usage options ## Print help

.PHONY: header
header:
	@printf "\033[34mEnvironment\033[0m"
	@echo ""
	@printf "\033[34m---------------------------------------------------------------\033[0m"
	@echo ""
	@printf "\033[33m%-23s\033[0m" "APP_NAME"
	@printf "\033[35m%s\033[0m" $(APP_NAME)
	@echo ""
	@printf "\033[33m%-23s\033[0m" "APP_VERSION"
	@printf "\033[35m%s\033[0m" $(APP_VERSION)
	@echo ""
	@echo ""

.PHONY: usage
usage:
	@printf "\033[034mUsage\033[0m"
	@echo ""
	@printf "\033[34m---------------------------------------------------------------\033[0m"
	@echo ""
	@printf "\033[37m%-22s\033[0m %s\n" "make [options]"
	@echo ""

.PHONY: options
options:
	@printf "\033[34mOptions\033[0m"
	@echo ""
	@printf "\033[34m---------------------------------------------------------------\033[0m"
	@echo ""
	@perl -nle'print $& if m{^[a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

# Makefile commands

.PHONY: run
run: start

.PHONY: start
start: ## Start the server
	$(eval include .env)
	$(eval export $(sh sed 's/=.*//' .env))

	python main.py

# Database commands

.PHONY: migrate
migrate: ## Run the migrations
	$(eval include .env)
	$(eval export $(sh sed 's/=.*//' .env))

	alembic upgrade head

.PHONY: rollback
rollback: ## Rollback the migrations
	$(eval include .env)
	$(eval export $(sh sed 's/=.*//' .env))

	alembic downgrade -1

.PHONY: generate-migration
generate-migration: ## Generate a new migration
	$(eval include .env)
	$(eval export $(sh sed 's/=.*//' .env))

	@printf "\033[33mEnter migration message: \033[0m"
	@read -r message; \
	alembic revision --autogenerate -m "$$message"
	@make lint migration

# Code quality commands

.PHONY: check
check: check-format lint

.PHONY: check-format
check-format: ## Check format
	-black ./ --check
	-ruff check --select I --select W --select E

.PHONY: lint
lint: ## Lint the code
	black ./
	ruff check --fix --select I --select W --select E
