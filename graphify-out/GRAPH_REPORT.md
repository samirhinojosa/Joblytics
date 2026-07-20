# Graph Report - Joblytics  (2026-07-20)

## Corpus Check
- 42 files · ~8,671 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 238 nodes · 344 edges · 33 communities (30 shown, 3 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 47 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0f4f28b7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- LinkedInConfig
- HttpPolicy
- Settings
- get_settings
- RawJobOffer
- .web_page_search
- job_offer.py
- Joblytics
- NoOffersFoundError
- linkedIn_scrapper
- .header
- joblytics
- 🧑‍💻 Command Line Interface (Typer)
- CLAUDE.md
- README.md

## God Nodes (most connected - your core abstractions)
1. `HttpPolicy` - 20 edges
2. `ScrapeClient` - 19 edges
3. `LinkedInConfig` - 14 edges
4. `Settings` - 11 edges
5. `RandomHeaderProvider` - 11 edges
6. `DummyHeaderProvider` - 11 edges
7. `get_settings()` - 10 edges
8. `LinkedInClient` - 10 edges
9. `LinkedInParser` - 10 edges
10. `RawJobOffer` - 9 edges

## Surprising Connections (you probably didn't know these)
- `test_web_page_last_attempt_retryable_raises_scrape_client_error()` --indirect_call--> `ScrapeClientError`  [INFERRED]
  tests/unit/infrastructure/http/scraping/test_http_client.py → src/joblytics/infrastructure/http/scraping/errors.py
- `test_compute_log_file_verbose()` --calls--> `compute_log_file()`  [INFERRED]
  tests/unit/core/test_settings.py → src/joblytics/core/config/logger.py
- `DummyHeaderProvider` --uses--> `HttpPolicy`  [INFERRED]
  tests/unit/infrastructure/http/scraping/test_http_client.py → src/joblytics/core/config/policy.py
- `settings()` --calls--> `get_settings()`  [INFERRED]
  tests/unit/core/test_settings.py → src/joblytics/core/config/settings.py
- `test_compute_log_file_verbose()` --calls--> `get_settings()`  [INFERRED]
  tests/unit/core/test_settings.py → src/joblytics/core/config/settings.py

## Import Cycles
- None detected.

## Communities (33 total, 3 thin omitted)

### Community 0 - "LinkedInConfig"
Cohesion: 0.08
Nodes (21): LinkedInClient, HttpUrl, Response, Builds the LinkedIn job search URL for both initial search and pagination, Constructs the URL to fetch the full details of a specific job offer.          A, Executes a network request to a specific LinkedIn URL.          This method acts, LinkedInConfig, BaseModel (+13 more)

### Community 1 - "HttpPolicy"
Cohesion: 0.14
Nodes (28): HttpPolicy, Return the (connect_timeout, read_timeout) tuple.          Returns:, HTTP execution policy for a scraping client.      This model defines all operati, BaseModel, RandomHeaderProvider, Return the UAs list loaded., BaseModel, HTTP scraping client with retry, backoff, throttling and provider-based policy c (+20 more)

### Community 2 - "Settings"
Cohesion: 0.16
Nodes (12): BaseSettings, PolicyResolver, BaseModel, HTTP policy resolver.      Responsible for selecting and composing the correct H, Resolve the HTTP policy for a given provider.          The resolution logic merg, LogLevel, Enum, Path (+4 more)

### Community 3 - "get_settings"
Cohesion: 0.12
Nodes (16): Self, main(), CLI of project utilities., compute_log_file(), Path, Logging policy:       - App logs (joblytics.*): INFO by default, DEBUG with --ve, setup_logging(), get_settings() (+8 more)

### Community 4 - "RawJobOffer"
Cohesion: 0.24
Nodes (9): ABC, RawJobOffer, BaseJobPipeline, PipelineReport, Enum, str, Template Method base class for Joblytics pipelines.      Subclasses must impleme, TimePosted (+1 more)

### Community 5 - ".web_page_search"
Cohesion: 0.15
Nodes (8): RuntimeError, HttpUrl, ScrapeClientError, HttpUrl, Response, Execute a GET request with retry, backoff, throttling and error handling., Compute exponential backoff delay with jitter and maximum cap.          Used for, Apply rate limiting based on provider policy.          Introduces a controlled d

### Community 6 - "job_offer.py"
Cohesion: 0.26
Nodes (10): ContractType, JobOfferBase, NormalizedJobOffer, BaseModel, Enum, str, Canonical job offer entity (provider-agnostic).      Providers must normalize th, Unique internal ID to avoid duplicates in the database. (+2 more)

### Community 7 - "Joblytics"
Cohesion: 0.08
Nodes (23): 🔹 Built-in safety mechanisms, 🚀 Common database (Docker) commands, 🐘 Database setup (PostgreSQL), Debug mode, Default production log path, ✅ Development mode (main + dev dependencies), Development Workflow (Makefile), ⚙️ Environment variables (.env) (+15 more)

### Community 8 - "NoOffersFoundError"
Cohesion: 0.33
Nodes (5): Exception, DomainError, NoOffersFoundError, HttpUrl, Basis for domain errors (non-technical).

### Community 9 - "linkedIn_scrapper"
Cohesion: 0.28
Nodes (8): linkedIn_scrapper(), Extracts job postings from LinkedIn and displays a summary table in the console., Any, Truncate a value for safe console display.      Converts any value to string and, Render a formatted table for console (CLI) output.      This function is respons, render_table(), truncate(), WorkModality

### Community 23 - "🧑‍💻 Command Line Interface (Typer)"
Cohesion: 0.18
Nodes (11): 🧑‍💻 Command Line Interface (Typer), Default behavior (no table), ⏱ Filter by publication date (time_posted), 🏢 Filter by work modality (work_modality), 🌍 Global options, 📋 Output rendering (CLI), ▶️ Scraping LinkedIn Jobs, 🔍 Show CLI help (+3 more)

### Community 29 - "CLAUDE.md"
Cohesion: 0.22
Nodes (8): Architecture Mapping, Coding Standards (dbt & Snowflake), Coding Standards & Pre-commit Rules, dbt (Transformation), Golden Rules, Joblytics (Ingestion), Role, Terminal & Execution Commands

## Knowledge Gaps
- **36 isolated node(s):** `joblytics`, `Role`, `Joblytics (Ingestion)`, `dbt (Transformation)`, `Coding Standards & Pre-commit Rules` (+31 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ScrapeClient` connect `HttpPolicy` to `LinkedInConfig`, `get_settings`, `.web_page_search`?**
  _High betweenness centrality (0.274) - this node is a cross-community bridge._
- **Why does `LinkedInClient` connect `LinkedInConfig` to `HttpPolicy`?**
  _High betweenness centrality (0.224) - this node is a cross-community bridge._
- **Why does `LinkedInPipeline` connect `LinkedInConfig` to `NoOffersFoundError`, `linkedIn_scrapper`, `RawJobOffer`?**
  _High betweenness centrality (0.140) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `HttpPolicy` (e.g. with `LogLevel` and `RuntimeSettings`) actually correct?**
  _`HttpPolicy` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `ScrapeClient` (e.g. with `HttpPolicy` and `RandomHeaderProvider`) actually correct?**
  _`ScrapeClient` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `LinkedInConfig` (e.g. with `LinkedInClient` and `TimePosted`) actually correct?**
  _`LinkedInConfig` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `Settings` (e.g. with `HttpPolicy` and `PolicyResolver`) actually correct?**
  _`Settings` has 2 INFERRED edges - model-reasoned connections that need verification._