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
- Docker Compose

## ▶️ Running the Project (Scraping LinkedIn Jobs)
```bash
python main.py
```

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

### 🐘 Database setup (PostgreSQL)
Joblytics uses PostgreSQL 16.4 as its local development database.</br>
The database is orchestrated through Docker Compose, ensuring consistent environments and easy teardown/rebuild.

#### ⚙️ Environment variables (.env)
```bash
# Database credentials
POSTGRES_USER=joblytics
POSTGRES_PASSWORD=joblytics_pwd
POSTGRES_DB=joblytics_db
```
🧠 Tip: keep your `.env` file out of version control if you ever store real credentials.

#### 🚀 Common database (Docker) commands
| Action                               | Command                           |
| ------------------------------------ | --------------------------------- |
| Start the database                   | `docker compose up -d postgres`   |
| Check status                         | `docker compose ps`               |
| Stop database                        | `docker compose stop postgres`    |
| Restart database                     | `docker compose restart postgres` |
| Remove container but keep data       | `docker compose down`             |
| Remove everything (including volume) | `docker compose down -v`          |

### 📝 Log files
#### ⚙️ Environment variables (.env)
```bash
# Log path
LOG_FILE=/var/log/joblytics/app.log
```
#### Log file permissions (important)
If you see a PermissionError, fix it with:

```bash
sudo mkdir -p /var/log/joblytics
sudo touch /var/log/joblytics/app.log
sudo chown $USER:$USER /var/log/joblytics/app.log
sudo chmod 664 /var/log/joblytics/app.log
```

### 🧪 Tests and Quality Checks (Development mode)
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
    ├── docker-compose.yml          # Local PostgreSQL setup for development
    ├── main.py                     # Entry point for scraping workflows (start here)
    ├── Makefile                    # Developer automation: install, lint, test, coverage, quality gates
    ├── LICENSE
    ├── poetry.lock
    ├── pyproject.toml              # Poetry configuration
    └── README.md

## 🧪 Notebooks & Experimental Development (Marimo or Jupyterlab)
The project includes a /notebooks directory intended for:
- Data exploration
- Rapid prototyping
- Testing ideas before integrating them into the core codebase
- Developing scrapers, transformations, or analysis drafts
- Interactive workflows using marimo

### Marimo
You can create/open marimo-ready notebooks interactively:
```bash
make marimo NB=my_experiment
```
Marimo provides an interactive development UI that behaves similarly to Jupyter but is fully Python-native and reproducible.

### Jupyter Lab
You can open the Jupyter Lab environment as follows:
```bash
make jupyterlab
```
