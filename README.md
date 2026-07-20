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

## 🧑‍💻 Command Line Interface (Typer)

Joblytics exposes a typed, documented CLI built with Typer, designed for reproducible scraping workflows and scripting.

### 🔍 Show CLI help
```bash
joblytics --help
```

### 🌍 Global options
These options apply to __all commands__.
| Option      | Alias | Description                |
| ----------- | ----- | -------------------------- |
| `--verbose` | `-v`  | Enable DEBUG-level logging |
|             |       | Default level logging      |


Example:<br>
ℹ️ When `--verbose` or `-v` is enabled, the application initializes logging with `DEBUG` level instead of `INFO`.
```bash
joblytics --verbose linkedin "Data Engineer" Paris
joblytics -v linkedin "Data Engineer" Paris
```
Default (as follows): `INFO` level logging
```bash
joblytics linkedin "Data Engineer" Paris
```

### ▶️ Scraping LinkedIn Jobs

```bash
joblytics linkedin "Data Engineer" Grenoble
```

### ⏱ Filter by publication date (time_posted)
The `time_posted` argument allows filtering offers by publication recency.<br>
`day` is the value by default.
```bash
joblytics "Data Engineer" Paris week
```

### Supported values
| Value   | Meaning                       |
| ------- | ----------------------------- |
| `all`   | All available offers          |
| `day`   | Published in the last 24h     |
| `week`  | Published in the last 7 days  |
| `month` | Published in the last 30 days |

ℹ️ The CLI values are mapped internally to LinkedIn technical filters (r86400, r604800, etc.), but remain human-readable at CLI level.

### 🏢 Filter by work modality (work_modality)
The `work_modality` argument allows filtering offers by publication recency.<br>
`all` is the value by default.
```bash
joblytics "Data Engineer" Paris day onsite
```

### Supported values
| Value   | Meaning                       |
| ------- | ----------------------------- |
| `all`   | All available offers          |
| `onsite`   | On-site positions (physical presence)     |
| `hybrid`  | Hybrid positions (office + remote mix)  |
| `remote` | Fully remote positions |

ℹ️ The CLI values are mapped internally to LinkedIn technical filters (1, 2, etc.), but remain human-readable at CLI level.

### 📋 Output rendering (CLI)
By default, __no table is displayed in the console__.

#### Show summary table in console

```bash
joblytics linkedin "Data Engineer" Grenoble --show-table
```

#### Default behavior (no table)
```bash
joblytics linkedin "Data Engineer" Grenoble
```
ℹ️ The --show-table flag enables rendering of a formatted summary table in the console output.<br>
Without this flag, the CLI runs in silent/data mode, suitable for pipelines, cron jobs, and integrations.

## 🚀 Installation

### ✅ Development mode (main + dev dependencies)
Install all dependencies including development tools:

```bash
make install
```
Includes: linters | formatters | typing | testing | notebooks | quality tooling

### ✅ Production mode (main dependencies only)
Recommended for deployment or production-like environments:

```bash
make install-prod
```
Includes: project package | runtime dependencies | CLI (joblytics)

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
| Command                           | Action                               |
| --------------------------------- | ------------------------------------ |
| `docker compose up -d postgres`   | Start the database                   |
| `docker compose ps`               | Check status                         |
| `docker compose stop postgres`    | Stop database                        |
| `docker compose restart postgres` | Restart database                     |
| `docker compose down`             | Remove container but keep data       |
| `docker compose down -v`          | Remove everything (including volume) |

### 📝 Logging

#### Default production log path
```bash
LOG_FILE=/var/log/joblytics/app.log
```
#### Debug mode
With `--verbose` or `-v`, logs are automatically written to:
```bash
LOG_FILE=/logs/joblytics.log
```
#### Log file permissions (important)
If you see a PermissionError, fix it with:

```bash
sudo mkdir -p /var/log/joblytics
sudo touch /var/log/joblytics/app.log
sudo chown $USER:$USER /var/log/joblytics/app.log
sudo chmod 664 /var/log/joblytics/app.log
```

###  Development Workflow (Makefile)
The Makefile provides a standardized development workflow: <br>
To execute: `make Command`

| Command                   | Description                                                                   |
| --------------------------| ------------------------------------------------------------------------------|
| `graphify-update`         | Rebuild and update the Graphify static analysis architecture map              |
| `check-imports`           | Ensure package import works and src.* imports are not required                |
| `check-no-src-imports`    | ail if code imports from src.joblytics                                        |
| `clean-all`               | Remove all caches and .venv                                                   |
| `clean`                   | Remove Python and tool caches (mypy, pytest, ruff, notebooks)                 |
| `cov-strict`              | Run tests with coverage (fail under a certain %)                              |
| `cov`                     | Run tests with coverage (without --cov-fail-under)                            |
| `fmt`                     | Format code (Ruff formatter) and apply safe lint autofixes                    |
| `format`                  | Format, lint, and type-check only (no tests)                                  |
| `lint`                    | Lint code with Ruff (no changes applied)                                      |
| `quality`                 | Format, lint, type-check, and run tests with coverage (pre-commit/pre-push)   |
| `test`                    | Run all tests (pytest)                                                        |
| `type`                    | Run MyPy on src/joblytics & tests (static type checking)                      |

## 📂 Project Structure (overview)
    .
    ├── dbt_project/                    # dbt Core models, macros, and seeds for Snowflake analytics
    │   ├── models/                     # Staging, intermediate, and marts transformation layers
    │   ├── dbt_project.yml             # dbt project configuration
    │   └── profiles.yml                # Warehouse profiles (Snowflake targets)
    │
    ├── src
    │   ├── joblytics
    │   │   ├── core                    # Central application configuration
    │   │   │   ├── config              # Settings, environment, logging and infrastructure policies (HttpPolicy/PolicyResolver)
    │   │   │   └── utils               # Cross-cutting helpers
    │   │   │
    │   │   ├── domain                  # Business rules, domain models, invariants
    │   │   │   ├── entities            # Domain entities (business models and invariants)
    │   │   │   └── exceptions          # Domain-level exceptions and business-rule violations
    │   │   │
    │   │   ├── infrastructure          # Technical implementations (IO, network, persistence)
    │   │   │   ├── http                # HTTP clients and scraping infrastructure
    │   │   │   │   └── scraping
    │   │   │   └── repositories        # Concrete implementations of data access (DB, cache, etc.)
    │   │   │
    │   │   ├── pipelines               # Provider-specific data pipelines (scraping + parsing + normalization)
    │   │   │   ├── base.py             # Shared pipeline contracts and core enums (WorkModality/TimePosted)
    │   │   │   └── linkedin
    │   │   │
    │   └── └── cli.py                  # Typer-based CLI entrypoint for scraping workflows (start here)
    │
    ├── notebooks                       # Experimental development area (marimo notebooks)
    │
    ├── tests                           # Unit and integration tests
    │
    ├── docker-compose.yml              # Local PostgreSQL setup for development
    ├── Makefile                        # Developer automation: install, lint, test, coverage, quality gates
    ├── LICENSE
    ├── poetry.lock
    ├── pyproject.toml                  # Poetry configuration
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

## 🤖 AI-Assisted Development & Architecture Enforcement

Joblytics is optimized for AI-assisted engineering. It couples static code-graph visualization with strict architectural guardrails, enabling agents (like Claude Code) to operate with maximum context efficiency and near-zero token waste.

### 🛠 Integrated Tooling
*   **Graphify:** Performs continuous static analysis across Python and dbt files, mapping architectural boundaries, nodes, and dependency layers without incurring LLM costs.
*   **Agent Skills:** Provides pre-compiled automated context hooks that minimize prompt overhead in the terminal sandbox.
*   **Architecture Enforcement (`CLAUDE.md`):** Enforces a strict unidirectional dependency rule: `Core/Domain → Infrastructure`. Infrastructure dependencies inside the `domain/` directory are blocked at the environment level.

### 🔄 The Token-Saving Development Lifecycle
To maintain context integrity and avoid context window pollution (which drastically reduces token costs), always follow this deterministic 5-step lifecycle when changing tasks or prompts with Claude Code:
```
[1. Code] -> [2. make quality] -> [3. Commit] -> [4. Graph Update] -> [5. exit]
```

1.  **Execute Changes:** Perform your atomic refactoring, feature implementation, or bug fix.
2.  **Verify Integrity:** Run the full quality control suite to guarantee type safety and code coverage:
    ```bash
    make quality
    ```
3.  **Commit Permanence:** Consolidate your progress with a clean, descriptive Git commit message.
4.  **Rebuild the Code Graph:** Synchronize the structural changes with Graphify so the AI workspace reflects the exact current state of the architecture:
    ```bash
    make graphify-update
    ```
5.  **Flush Agent Memory (`exit`):** Type `exit` or `quit` to close the active Claude Code session.

> ⚠️ **Crucial Rule:** Never carry context from a finished task into a new, unrelated query. Exiting the chat clears out stale intermediate traces, execution errors, and redundant file readings. When you launch a fresh `claude` instance, the agent starts with 0% memory overhead—consuming up to 80% fewer tokens and strictly operating on the updated code graph map.


## ⚖️ Responsible Use & Platform Compliance

Joblytics is designed as a research, analytics, and engineering platform, not as a mass scraping tool.
Special care is taken with sensitive platforms such as LinkedIn.

The project enforces a responsible scraping policy based on the following principles:

### 🔹 Responsible usage
    Joblytics is intended for:
    - research
    - analytics
    - educational use
    - labor market studies
    - experimentation
    - data engineering practice

    Not for:
    - mass automation abuse
    - data resale
    - aggressive crawling
    - commercial exploitation of scraped content
    - platform degradation

### 🔹 Built-in safety mechanisms
    The system is designed to support:
    - Default rate limiting
    - Request throttling
    - Progressive backoff strategies
    - Header rotation
    - User-agent rotation
    - Timeout control
    - Failure-aware retry logic
    - Dry-run mode (no network calls)
    - Robots.txt respect
    - Platform-aware crawling profiles

### 🔹 LinkedIn-specific sensitivity
    LinkedIn is particularly sensitive to automated access.<br>
    For this reason, Joblytics includes:
    - conservative default request rates
    - enforced delays between requests
    - adaptive retry/backoff logic
    - identifiable user-agent headers
    - request randomization
    - safety-first defaults

### 🔹 Ethical and engineering disclaimer
    This project does not provide legal advice.<br>
    Users are responsible for:
    - respecting platform terms of service
    - complying with local laws and regulations
    - using the system ethically
    - ensuring legitimate use cases

Joblytics focuses on __engineering responsibility__, not legal interpretation.
