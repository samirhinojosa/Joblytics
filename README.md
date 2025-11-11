# Joblytics

Joblytics is a Python-based tool to scrape and analyse job listings from platforms such as LinkedIn, Welcome to the Jungle, among others.</br>
It provides a clean, modular architecture for ingesting job data, transforming it, and enabling downstream analytics.

## 🎯 Project Goals

Joblytics aims to provide a modern, scalable and modular framework to:

- Collect job market data from multiple platforms using robust scraping workflows.
- Standardize and validate job information through domain models and Pydantic schemas.
- Enable fast experimentation through interactive marimo notebooks for prototyping and exploratory analysis.
- Support downstream analytics (skills extraction, trend analysis, salary patterns, etc.).
- Encourage clean architecture practices, separating domain, infrastructure, and application logic.
- Serve as a foundation for ML-based insights such as job classification, skill clustering, or recommendation systems.

## Requirements
- Python 3.12 (recommended)
- Poetry

## 📂 Project Structure (overview)
    .
    ├── app
        ├── core                    # Central application configuration (settings, environment, logging)
        ├── domain
            ├── exceptions          # Domain-level exceptions and business-rule violations
            ├── schemas             # Pydantic models (DTOs) for validation and serialization
        ├── infrastructure
            ├── http                # HTTP client, scraper utilities, and header providers
            ├── ingestion           # Scrapers and data ingestion workflows
            ├── repositories        # Concrete implementations of data access (DB, cache, etc.)
            ├── services            # Integrations with external services/APIs (e.g., ML, third-party APIs)
    ├── notebooks                   # Experimental development area (marimo notebooks)
    ├── test                        # Unit and integration tests
    ├── LICENSE
    ├── poetry.lock
    ├── pyproject.toml              # Poetry configuration
    └── README.md

## 🚀 Installation

### ✅ Development mode (main + dev dependencies)
Install all dependencies including development tools:

```bash
make install
```

### ✅ Production mode (main dependencies only)
Recommended for deployment or production-like environments:

```bash
make install-prod
```

### 📝 Log file permissions (important)

If the application writes to:

```bash
/var/log/joblytics/app.log
```

and you see a PermissionError, fix it with:

```bash
sudo mkdir -p /var/log/joblytics
sudo touch /var/log/joblytics/app.log
sudo chown $USER:$USER /var/log/joblytics/app.log
sudo chmod 664 /var/log/joblytics/app.log
```

### 🧪 Tests and Quality Checks
The Makefile provides a standardized development workflow:

| Command           | Description                                                      |
| ----------------- | ---------------------------------------------------------------- |
| `make test`       | Run all tests (pytest)                                           |
| `make cov`        | Run tests with coverage (no failure threshold)                   |
| `make cov-strict` | Run tests with coverage and enforce minimum %                    |
| `make lint`       | Lint code with Ruff (no changes applied)                         |
| `make fmt`        | Format code and apply safe Ruff fixes                            |
| `make type`       | Static type checking using MyPy                                  |
| `make format`     | Format + lint + type-check (no tests)                            |
| `make quality`    | Full quality gate: format, lint, type-check, and strict coverage |

### 🧪 Notebooks & Experimental Development (Marimo)
The project includes a /notebooks directory intended for:
- Data exploration
- Rapid prototyping
- Testing ideas before integrating them into the core codebase
- Developing scrapers, transformations, or analysis drafts
- Interactive workflows using marimo

You can create/open marimo-ready notebooks interactively:
```bash
make marimo NB=my_experiment
```
Marimo provides an interactive development UI that behaves similarly to Jupyter but is fully Python-native and reproducible.
