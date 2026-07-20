# Graph Report - Joblytics  (2026-07-20)

## Corpus Check
- 55 files · ~11,159 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 347 nodes · 600 edges · 36 communities (33 shown, 3 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 108 edges (avg confidence: 0.69)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5a1499c8`
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
1. `HttpPolicy` - 27 edges
2. `ScrapeClient` - 26 edges
3. `RawJobOffer` - 19 edges
4. `LinkedInParser` - 19 edges
5. `LinkedInClient` - 18 edges
6. `LinkedInConfig` - 17 edges
7. `LinkedInPipeline` - 16 edges
8. `DummyHeaderProvider` - 15 edges
9. `RandomHeaderProvider` - 14 edges
10. `_patch_settings()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `test_for_provider_merges_override_onto_default()` --calls--> `HttpPolicy`  [INFERRED]
  tests/unit/core/test_policy.py → src/joblytics/core/config/policy.py
- `test_for_provider_returns_default_when_no_override()` --calls--> `HttpPolicy`  [INFERRED]
  tests/unit/core/test_policy.py → src/joblytics/core/config/policy.py
- `test_truncate_long_value_is_ellipsized()` --calls--> `truncate()`  [INFERRED]
  tests/unit/core/test_utils_cli.py → src/joblytics/core/utils/cli.py
- `test_truncate_none_returns_empty_string()` --calls--> `truncate()`  [INFERRED]
  tests/unit/core/test_utils_cli.py → src/joblytics/core/utils/cli.py
- `test_truncate_short_value_is_unchanged()` --calls--> `truncate()`  [INFERRED]
  tests/unit/core/test_utils_cli.py → src/joblytics/core/utils/cli.py

## Import Cycles
- None detected.

## Communities (36 total, 3 thin omitted)

### Community 0 - "LinkedInConfig"
Cohesion: 0.08
Nodes (30): LinkedInClient, HttpUrl, Response, Builds the LinkedIn job search URL for both initial search and pagination, Constructs the URL to fetch the full details of a specific job offer.          A, Executes a network request to a specific LinkedIn URL.          This method acts, LinkedInConfig, BaseModel (+22 more)

### Community 1 - "HttpPolicy"
Cohesion: 0.13
Nodes (36): HttpPolicy, Return the (connect_timeout, read_timeout) tuple.          Returns:, HTTP execution policy for a scraping client.      This model defines all operati, BaseModel, RandomHeaderProvider, Return the UAs list loaded., BaseModel, HTTP scraping client with retry, backoff, throttling and provider-based policy c (+28 more)

### Community 2 - "Settings"
Cohesion: 0.11
Nodes (23): LinkedInParser, Any, Parses the rich description and criteria from a specific job page., Extracts the total number of jobs found from the search header., Extract the LinkedIn-specific geographic identifier (geoId) value from         t, Parses the search results list.         Distinguishes between mandatory and opti, Responsible for extracting structured data from raw HTML.     Does not perform n, _card_html() (+15 more)

### Community 3 - "get_settings"
Cohesion: 0.07
Nodes (28): BaseSettings, Self, compute_log_file(), Path, Logging policy:       - App logs (joblytics.*): INFO by default, DEBUG with --ve, setup_logging(), PolicyResolver, BaseModel (+20 more)

### Community 4 - "RawJobOffer"
Cohesion: 0.11
Nodes (25): ABC, RawJobOffer, BaseJobPipeline, PipelineReport, Enum, str, Template Method base class for Joblytics pipelines.      Subclasses must impleme, TimePosted (+17 more)

### Community 5 - ".web_page_search"
Cohesion: 0.15
Nodes (8): RuntimeError, HttpUrl, ScrapeClientError, HttpUrl, Response, Execute a GET request with retry, backoff, throttling and error handling., Compute exponential backoff delay with jitter and maximum cap.          Used for, Apply rate limiting based on provider policy.          Introduces a controlled d

### Community 6 - "job_offer.py"
Cohesion: 0.26
Nodes (10): ContractType, JobOfferBase, NormalizedJobOffer, BaseModel, Enum, str, Canonical job offer entity (provider-agnostic).      Providers must normalize th, Unique internal ID to avoid duplicates in the database. (+2 more)

### Community 7 - "Joblytics"
Cohesion: 0.06
Nodes (34): 🔹 Built-in safety mechanisms, 🧑‍💻 Command Line Interface (Typer), 🚀 Common database (Docker) commands, 🐘 Database setup (PostgreSQL), Debug mode, Default behavior (no table), Default production log path, ✅ Development mode (main + dev dependencies) (+26 more)

### Community 8 - "NoOffersFoundError"
Cohesion: 0.17
Nodes (20): DomainError, NoOffersFoundError, Exception, HttpUrl, Basis for domain errors (non-technical)., test_no_offers_found_error_is_a_domain_error(), test_no_offers_found_error_message_with_url(), test_no_offers_found_error_message_without_url() (+12 more)

### Community 9 - "linkedIn_scrapper"
Cohesion: 0.24
Nodes (11): Any, Truncate a value for safe console display.      Converts any value to string and, Render a formatted table for console (CLI) output.      This function is respons, render_table(), truncate(), test_render_table_drops_and_truncates_columns(), test_render_table_no_rows_returns_message(), test_render_table_uses_str_for_columns_without_limit() (+3 more)

### Community 23 - "🧑‍💻 Command Line Interface (Typer)"
Cohesion: 0.20
Nodes (15): linkedIn_scrapper(), main(), WorkModality, CLI of project utilities., Extracts job postings from LinkedIn and displays a summary table in the console., LinkedInPipeline, Executes the full LinkedIn scraping lifecycle: search, discovery, and enrichment, _no_op_logging() (+7 more)

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
  _High betweenness centrality (0.289) - this node is a cross-community bridge._
- **Why does `LinkedInClient` connect `LinkedInConfig` to `HttpPolicy`, `🧑‍💻 Command Line Interface (Typer)`?**
  _High betweenness centrality (0.280) - this node is a cross-community bridge._
- **Why does `LinkedInPipeline` connect `🧑‍💻 Command Line Interface (Typer)` to `LinkedInConfig`, `NoOffersFoundError`, `Settings`, `RawJobOffer`?**
  _High betweenness centrality (0.236) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `HttpPolicy` (e.g. with `LogLevel` and `RuntimeSettings`) actually correct?**
  _`HttpPolicy` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `ScrapeClient` (e.g. with `HttpPolicy` and `RandomHeaderProvider`) actually correct?**
  _`ScrapeClient` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `RawJobOffer` (e.g. with `BaseJobPipeline` and `PipelineReport`) actually correct?**
  _`RawJobOffer` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `LinkedInParser` (e.g. with `LinkedInPipeline` and `test_parse_job_details_extracts_description_time_and_criteria()`) actually correct?**
  _`LinkedInParser` has 10 INFERRED edges - model-reasoned connections that need verification._