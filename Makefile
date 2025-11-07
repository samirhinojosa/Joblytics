# Project settings
APP_NAME:=joblytics
APP_MODULE:=app.main:app
POETRY?=poetry
SRC:=app tests
PKG:=app
COV_FAIL_UNDER:=85

SHELL := /bin/bash
.DEFAULT_GOAL := help

# ---------------------------------------------
# Pretty help (auto-generates from '##' docs)
# ---------------------------------------------
# Usage: add '## Description' to each target line

# Disable color with: NO_COLOR=1 make help
ifeq ($(NO_COLOR),1)
	CYAN :=
	NC :=
else
	CYAN := \033[36m
	NC   := \033[0m
endif

.PHONY: clean clean-all cov cov-strict format fmt help install install-prod jupyter-lab lint quality test type

define LOG_FILE
	@LOG_FILE="$$( $(POETRY) run python -c 'from app.core.settings import get_settings; \
	settings=get_settings(); print(settings.LOG_FILE)' )"; \
	LOG_DIR="$$(dirname "$$LOG_FILE")"; \
	if [ -z "$$LOG_FILE" ]; then \
		echo "ERROR: LOG_FILE is empty (could not load settings)"; exit 1; \
	fi; \
	if [ ! -d "$$LOG_DIR" ]; then \
		echo "⚙️ Creating directory $$LOG_DIR"; \
		sudo mkdir -p "$$LOG_DIR"; \
	fi; \
	if [ ! -f "$$LOG_FILE" ]; then \
		echo "⚙️ Creating log file $$LOG_FILE"; \
		sudo touch "$$LOG_FILE"; \
		sudo chmod 664 "$$LOG_FILE"; \
	else \
		echo "✅ Log file already exists: $$LOG_FILE"; \
	fi
endef

define CLEAN
	@echo "🧹 Cleaning caches..."
	@find . -type d \( \
		 -name '__pycache__' -o \
		 -name '.mypy_cache' -o \
		 -name '.pytest_cache' -o \
		 -name '.ruff_cache' -o \
		 -name '.ipynb_checkpoints' \
	\) -prune -exec rm -rf {} +
	@find . -type f \( -name '*.pyc' -o -name '*.pyo' -o -name '*.py[co]' \) -exec rm -f {} +
	@echo "✅ All caches removed."
endef

define FORMAT
	@$(POETRY) run ruff format $(SRC)
	@$(POETRY) run ruff check --fix $(SRC)
	@$(POETRY) run mypy $(SRC)
endef

define COV-STRICT
	@$(POETRY) run pytest --cov=$(PKG) --cov-report=term-missing --cov-fail-under=$(COV_FAIL_UNDER)
endef

install: ## Install everything (main + dev dependencies)
	@$(POETRY) install --with dev
	@$(LOG_FILE)

install-prod: ## Install only production dependencies (no dev)
	@$(POETRY) install --only main --no-root
	@$(LOG_FILE)

jupyter-lab: ## Run Jupyter Lab (only if you installed the notebooks group)
	@$(POETRY) run jupyter lab

fmt: ## Format code (Ruff formatter) and apply safe lint autofixes
	@$(POETRY) run ruff format $(SRC)
	@$(POETRY) run ruff check --fix $(SRC)

lint: ## Lint code with Ruff (no changes)
	@$(POETRY) run ruff check $(SRC)

type: ## Run MyPy on /app & /tests (static type checking)
	@$(POETRY) run mypy $(SRC)

test: ## Run all tests (pytest)
	@$(POETRY) run pytest -q

cov: ## Run tests with coverage (without --cov-fail-under)
	@$(POETRY) run pytest --cov=$(PKG) --cov-report=term-missing

cov-strict: ## Run tests with coverage (fail under a certain %)
	@$(COV-STRICT)

format: ## Format, lint, and type-check only (no tests)
	@$(FORMAT)

quality:  ## Format, lint, type-check, and run tests with coverage (pre-commit/pre-push)
	@$(LINT)
	@$(COV-STRICT)

clean: ## Remove Python and tool caches (mypy, pytest, ruff, notebooks)
	@$(CLEAN)

clean-all: ## Remove all caches and .venv
	@$(CLEAN)
	@if [ -d ".venv" ]; then \
		echo "🧹 Removing .venv..."; \
		rm -rf .venv; \
		echo "✅  .venv removed."; \
	else \
		echo "✅  No .venv directory to remove."; \
	fi

help: ## Show this help
	@echo "Makefile commands:"
	@grep -E '^[a-zA-Z0-9_.-]+:.*?## ' $(MAKEFILE_LIST) \
	| sort \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-18s$(NC) %s\n", $$1, $$2}'
