# Project settings
APP_NAME:=joblytics
APP_MODULE:=joblytics.main:app
POETRY?=poetry
SRC:=src tests
PKG:=joblytics
COV_FAIL_UNDER:=85

NOTEBOOKS_DIR := notebooks

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

.PHONY: clean clean-all cov cov-strict format fmt help install install-prod lint marimo jupyterlab quality test type

define LOG_FILE
	@LOG_FILE="$$( $(POETRY) run python -c 'from joblytics.core.config.settings import get_settings; \
	settings=get_settings(); print(settings.LOG_FILE)' )"; \
	LOG_DIR="$$(dirname "$$LOG_FILE")"; \
	if [ -z "$$LOG_FILE" ]; then \
		echo "ERROR: LOG_FILE is empty (could not load settings)"; exit 1; \
	fi; \
	if [ ! -d "$$LOG_DIR" ]; then \
		echo "⚙️ Creating directory $$LOG_DIR"; \
		mkdir -p "$$LOG_DIR"; \
	fi; \
	if [ ! -f "$$LOG_FILE" ]; then \
		echo "⚙️ Creating log file $$LOG_FILE"; \
		touch "$$LOG_FILE"; \
		chmod 664 "$$LOG_FILE"; \
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
		 -name '.ipynb_checkpoints' -o \
		 -name '__marimo__' \
	\) -prune -exec rm -rf {} +
	@find . -type f \( -name '*.pyc' -o -name '*.pyo' -o -name '*.py[co]' \) -exec rm -f {} +
	@echo "✅ All caches removed."
endef

define FORMAT
	@$(POETRY) run ruff format $(SRC)
	@$(POETRY) run ruff check --fix $(SRC)
	@$(POETRY) run mypy src/joblytics tests
endef

define COV-STRICT
	@$(POETRY) run pytest --cov=$(PKG) --cov-report=term-missing --cov-fail-under=$(COV_FAIL_UNDER)
endef

install: ## Install everything (main + dev dependencies)
	@$(POETRY) lock
	@$(POETRY) install --with dev
	@$(LOG_FILE)

install-prod: ## Install only production dependencies (no dev)
	@$(POETRY) install --only main
	@$(LOG_FILE)

marimo: ## Run marimo on a given notebook: NB=my_experiment (will open notebooks/my_experiment.py)
	@if [ -z "$(NB)" ]; then \
		echo "❌ ERROR: You must provide NB=<notebook_name>"; \
		echo "   Example: make marimo NB=my_experiment"; \
		exit 1; \
	fi; \
	FILE="$(NOTEBOOKS_DIR)/$(NB).py"; \
	echo "📄 Notebook file: $$FILE"; \
	if [ ! -f "$$FILE" ]; then \
		echo "📄 File $$FILE does not exist, creating it..."; \
		$(POETRY) run marimo create "$$FILE"; \
	fi; \
	echo "🚀 Opening marimo with $$FILE"; \
	$(POETRY) run marimo edit "$$FILE" --headless

jupyterlab: ## Run Jupyter Lab on root
	@$(POETRY) run jupyter lab $(NOTEBOOKS_DIR)

fmt: ## Format code (Ruff formatter) and apply safe lint autofixes
	@$(POETRY) run ruff format $(SRC)
	@$(POETRY) run ruff check --fix $(SRC)

lint: ## Lint code with Ruff (no changes)
	@$(POETRY) run ruff check $(SRC)

type: ## Run MyPy on src/joblytics & tests (static type checking)
	@$(POETRY) run mypy src/joblytics tests

test: ## Run all tests (pytest)
	@$(POETRY) run pytest -q

cov: ## Run tests with coverage (without --cov-fail-under)
	@$(POETRY) run pytest --cov=$(PKG) --cov-report=term-missing

cov-strict: ## Run tests with coverage (fail under a certain %)
	@$(COV-STRICT)

format: ## Format, lint, and type-check only (no tests)
	@$(FORMAT)

quality:  ## Format, lint, type-check, and run tests with coverage (pre-commit/pre-push)
	@$(FORMAT)
	@$(COV-STRICT)
	@$(MAKE) check-imports
	@$(MAKE) check-no-src-imports

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

check-imports: ## Ensure package import works and src.* imports are not required
	@$(POETRY) run python -c "import joblytics; print(joblytics.__file__)"
	@cd /tmp && ! $(POETRY) run python -c "import src.joblytics" 2>/dev/null

check-no-src-imports: ## Fail if code imports from src.joblytics
	@! grep -R --line-number -E '(^\s*from\s+src\.joblytics|^\s*import\s+src\.joblytics)' src tests 2>/dev/null


help: ## Show this help
	@echo "Makefile commands:"
	@grep -E '^[a-zA-Z0-9_.-]+:.*?## ' $(MAKEFILE_LIST) \
	| sort \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-18s$(NC) %s\n", $$1, $$2}'
