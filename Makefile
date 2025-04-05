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


### Development

.PHONY: start
start: ## Start the server
	FASTAPI_ENV=development uv run python -m main


### Code quality

.PHONY: fix-lint
lint-fix: ## Auto-fix linting issues where possible
	uv run ruff check --fix .

.PHONE: format
format: ## Format the code
	uv run ruff format .

.PHONY: lint
lint: ## Check code for style and error issues
	uv run ruff check .
