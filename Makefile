.PHONY: install lint type-check test check fmt check-now clean

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

## Setup
install: $(VENV)/bin/activate ## Install dependencies + dev tools
$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install -e ".[dev]"
	$(VENV)/bin/pre-commit install

## Quality
lint: ## Run ruff linter
	$(VENV)/bin/ruff check src/ tests/ main.py

fmt: ## Auto-format code
	$(VENV)/bin/ruff check --fix src/ tests/ main.py
	$(VENV)/bin/ruff format src/ tests/ main.py

type-check: ## Run mypy type checker
	$(VENV)/bin/mypy src/ main.py

test: ## Run tests
	$(VENV)/bin/pytest -v

check: lint type-check test ## Run all checks (lint + types + tests)

## Run
check-now: ## Run a single inventory check locally
	RESULTS_DIR=./results $(PYTHON) main.py

## Docker
docker-build: ## Build Docker image locally
	docker build -t tesla-checker .

docker-run: ## Run Docker image locally
	docker run --rm -e NTFY_TOPIC=$${NTFY_TOPIC} -v $$(pwd)/results:/data tesla-checker

## Cleanup
clean: ## Remove venv and caches
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache *.egg-info results/

## Help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
