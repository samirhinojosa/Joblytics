# Project settings
APP_NAME:=joblytics
APP_MODULE:=app.main:app
POETRY?=poetry
SRC:=app tests
PKG:=app

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

.PHONY: install jupyter-lab fmt lint type test cov check clean help

install: ## Install dependencies via Poetry (with dev)
	@$(POETRY) install --with dev

jupyter-lab: ## Run Jupyter Lab (only if you installed the notebooks group)
	@$(POETRY) run jupyter lab

fmt: ## Format code (Ruff formatter) and apply safe lint autofixes
	@$(POETRY) run ruff format $(SRC)
	@$(POETRY) run ruff check --fix $(SRC)

lint: ## Lint code with Ruff (no changes)
	@$(POETRY) run ruff check $(SRC)

type: ## Run MyPy on $(PKG)/ (static type checking)
	@$(POETRY) run mypy $(SRC)

test: ## Run all tests (pytest)
	@$(POETRY) run pytest -q

cov: ## Run tests with coverage (fail under 90%)
	@$(POETRY) run pytest --cov=$(PKG) --cov-report=term-missing --cov-fail-under=90

# Full local quality gate (good pre-commit/pre-push)
check: ## Run: fmt, lint, type, cov (full local quality gate — good pre-commit/pre-push)
	@$(POETRY) run ruff format $(SRC)
	@$(POETRY) run ruff check --fix $(SRC)
	@$(POETRY) run mypy $(SRC)
	@$(POETRY) run pytest --cov=$(PKG) --cov-report=term-missing --cov-fail-under=90

clean: ## Clean Python cache files. Remove __pycache__ and .pyc, .pyo, .py[co] files
	@find . -type d -name '__pycache__' -prune -exec rm -rf {} + -o \
		-type f \( -name '*.pyc' -o -name '*.pyo' -o -name '*.py[co]' \) -exec rm -f {} +

help: ## Show this help
	@echo "Makefile commands:"
	@grep -E '^[a-zA-Z0-9_.-]+:.*?## ' $(MAKEFILE_LIST) \
	| sort \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-18s$(NC) %s\n", $$1, $$2}'


