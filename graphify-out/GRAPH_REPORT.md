# Graph Report - Joblytics  (2026-07-22)

## Corpus Check
- 97 files · ~63,575 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 990 nodes · 1280 edges · 71 communities (67 shown, 4 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 139 edges (avg confidence: 0.67)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `46d205ca`
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
- my_first_dbt_model.sql
- my_second_dbt_model.sql
- _config
- raw_linkedin_jobs.sql
- Browser Testing with DevTools
- Shipping and Launch
- API and Interface Design
- CI/CD and Automation
- Deprecation and Migration
- Frontend UI Engineering
- Context Engineering
- Incremental Implementation
- Code Simplification
- Debugging and Error Recovery
- Documentation and ADRs
- Performance Optimization
- ReOrder: Keep Your Regulars Ordering Direct
- Interview Me
- Planning and Task Breakdown
- Doubt-Driven Development
- Idea Refine
- Process
- Using Agent Skills
- Spec-Driven Development
- Refinement & Evaluation Criteria
- Source-Driven Development
- Spec: Welcome to the Jungle (WTTJ) Job Scraper
- Ideation Frameworks Reference
- _config
- idea-refine.sh

## God Nodes (most connected - your core abstractions)
1. `RawJobOffer` - 33 edges
2. `HttpPolicy` - 27 edges
3. `ScrapeClient` - 26 edges
4. `LinkedInParser` - 19 edges
5. `Code Review and Quality` - 19 edges
6. `LinkedInClient` - 18 edges
7. `LinkedInPipeline` - 18 edges
8. `LinkedInConfig` - 17 edges
9. `_FakePipeline` - 16 edges
10. `Security and Hardening` - 16 edges

## Surprising Connections (you probably didn't know these)
- `_settings()` --calls--> `get_settings()`  [INFERRED]
  tests/unit/infrastructure/repositories/test_snowflake_raw_job_offer_repository.py → src/joblytics/core/config/settings.py
- `test_truncate_long_value_is_ellipsized()` --calls--> `truncate()`  [INFERRED]
  tests/unit/core/test_utils_cli.py → src/joblytics/core/utils/cli.py
- `test_truncate_none_returns_empty_string()` --calls--> `truncate()`  [INFERRED]
  tests/unit/core/test_utils_cli.py → src/joblytics/core/utils/cli.py
- `test_truncate_short_value_is_unchanged()` --calls--> `truncate()`  [INFERRED]
  tests/unit/core/test_utils_cli.py → src/joblytics/core/utils/cli.py
- `test_render_table_drops_and_truncates_columns()` --calls--> `render_table()`  [INFERRED]
  tests/unit/core/test_utils_cli.py → src/joblytics/core/utils/cli.py

## Import Cycles
- None detected.

## Communities (71 total, 4 thin omitted)

### Community 0 - "LinkedInConfig"
Cohesion: 0.09
Nodes (23): LinkedInClient, HttpUrl, Response, Builds the LinkedIn job search URL for both initial search and pagination, Constructs the URL to fetch the full details of a specific job offer.          A, Executes a network request to a specific LinkedIn URL.          This method acts, LinkedInConfig, BaseModel (+15 more)

### Community 1 - "HttpPolicy"
Cohesion: 0.07
Nodes (52): HttpPolicy, PolicyResolver, BaseModel, Return the (connect_timeout, read_timeout) tuple.          Returns:, HTTP policy resolver.      Responsible for selecting and composing the correct H, HTTP execution policy for a scraping client.      This model defines all operati, Resolve the HTTP policy for a given provider.          The resolution logic merg, HttpUrl (+44 more)

### Community 2 - "Settings"
Cohesion: 0.11
Nodes (23): LinkedInParser, Any, Parses the rich description and criteria from a specific job page., Extracts the total number of jobs found from the search header., Extract the LinkedIn-specific geographic identifier (geoId) value from         t, Parses the search results list.         Distinguishes between mandatory and opti, Responsible for extracting structured data from raw HTML.     Does not perform n, _card_html() (+15 more)

### Community 3 - "get_settings"
Cohesion: 0.09
Nodes (23): BaseSettings, Self, compute_log_file(), Path, Logging policy:       - App logs (joblytics.*): INFO by default, DEBUG with --ve, setup_logging(), get_settings(), LogLevel (+15 more)

### Community 4 - "RawJobOffer"
Cohesion: 0.08
Nodes (38): ABC, Protocol, RawJobOffer, Persist a batch of raw job offers exactly as scraped.          Args:, Port for persisting raw, unmodified job offers (Bronze/RAW layer)., RawJobOfferRepository, BaseJobPipeline, PipelineReport (+30 more)

### Community 5 - ".web_page_search"
Cohesion: 0.07
Nodes (29): 1. Correctness, 2. Readability & Simplicity, 3. Architecture, 4. Security, 5. Performance, Change Descriptions, Change Sizing, Code Review and Quality (+21 more)

### Community 6 - "job_offer.py"
Cohesion: 0.26
Nodes (10): ContractType, JobOfferBase, NormalizedJobOffer, BaseModel, Enum, str, Canonical job offer entity (provider-agnostic).      Providers must normalize th, Unique internal ID to avoid duplicates in the database. (+2 more)

### Community 7 - "Joblytics"
Cohesion: 0.05
Nodes (40): 🤖 AI-Assisted Development & Architecture Enforcement, 🔹 Built-in safety mechanisms, 🧑‍💻 Command Line Interface (Typer), 🚀 Common database (Docker) commands, 🐘 Database setup (PostgreSQL), Debug mode, Default behavior (no table), Default production log path (+32 more)

### Community 8 - "NoOffersFoundError"
Cohesion: 0.17
Nodes (20): DomainError, NoOffersFoundError, Exception, HttpUrl, Basis for domain errors (non-technical)., test_no_offers_found_error_is_a_domain_error(), test_no_offers_found_error_message_with_url(), test_no_offers_found_error_message_without_url() (+12 more)

### Community 9 - "linkedIn_scrapper"
Cohesion: 0.24
Nodes (11): Any, Truncate a value for safe console display.      Converts any value to string and, Render a formatted table for console (CLI) output.      This function is respons, render_table(), truncate(), test_render_table_drops_and_truncates_columns(), test_render_table_no_rows_returns_message(), test_render_table_uses_str_for_columns_without_limit() (+3 more)

### Community 10 - ".header"
Cohesion: 0.10
Nodes (19): Exception, RuntimeError, SnowflakeLoadError, Path, Serialize a batch of raw job offers to a gzip-compressed NDJSON file.          A, Persists RawJobOffer batches, unmodified, into Snowflake's RAW (Bronze) layer., Persist a batch of raw job offers into the Snowflake RAW table.          Seriali, SnowflakeRawJobOfferRepository (+11 more)

### Community 23 - "🧑‍💻 Command Line Interface (Typer)"
Cohesion: 0.24
Nodes (16): linkedIn_scrapper(), main(), WorkModality, CLI of project utilities., Extracts job postings from LinkedIn and displays a summary table in the console., LinkedInPipeline, _no_op_logging(), MonkeyPatch (+8 more)

### Community 29 - "CLAUDE.md"
Cohesion: 0.22
Nodes (8): Architecture Mapping, Coding Standards (dbt & Snowflake), Coding Standards & Pre-commit Rules, dbt (Transformation), Golden Rules, Joblytics (Ingestion), Role, Terminal & Execution Commands

### Community 31 - "my_first_dbt_model.sql"
Cohesion: 0.07
Nodes (29): Always Do (No Exceptions), Ask First (Requires Human Approval), Broken Access Control, Broken Authentication, Common Rationalizations, Cross-Site Scripting (XSS), File Upload Safety, Injection (SQL, NoSQL, OS Command) (+21 more)

### Community 32 - "my_second_dbt_model.sql"
Cohesion: 0.07
Nodes (29): Browser Testing with DevTools, Common Rationalizations, DAMP Over DRY in Tests, Decision Guide, Discover the Stack First, Name Tests Descriptively, One Assertion Per Concept, Overview (+21 more)

### Community 36 - "_config"
Cohesion: 0.07
Nodes (26): 1. Commit Early, Commit Often, 2. Atomic Commits, 3. Descriptive Messages, 4. Keep Concerns Separate, 5. Size Your Changes, Branch Naming, Branching Strategy, Change Summaries (+18 more)

### Community 41 - "Browser Testing with DevTools"
Cohesion: 0.08
Nodes (24): Accessibility Verification with DevTools, Available Tools, Browser Testing with DevTools, Clean Console Standard, Common Rationalizations, Console Analysis Patterns, Content Boundary Markers, For Network Issues (+16 more)

### Community 42 - "Shipping and Launch"
Cohesion: 0.08
Nodes (24): Accessibility, Code Quality, Common Rationalizations, Documentation, Error Reporting, Feature Flag Strategy, Infrastructure, Monitoring and Observability (+16 more)

### Community 43 - "API and Interface Design"
Cohesion: 0.08
Nodes (23): 1. Contract First, 2. Consistent Error Semantics, 3. Validate at Boundaries, 4. Prefer Addition Over Modification, 5. Predictable Naming, API and Interface Design, Common Rationalizations, Core Principles (+15 more)

### Community 44 - "CI/CD and Automation"
Cohesion: 0.08
Nodes (23): Automation Beyond CI, Basic CI Pipeline, Build Cop Role, CI/CD and Automation, CI Optimization, Common Rationalizations, Dependabot / Renovate, Deployment Strategies (+15 more)

### Community 45 - "Deprecation and Migration"
Cohesion: 0.08
Nodes (23): Adapter Pattern, Code Is a Liability, Common Rationalizations, Compulsory vs Advisory Deprecation, Core Principles, Database Schema Migrations (Expand/Contract), Deprecation and Migration, Deprecation Planning Starts at Design Time (+15 more)

### Community 46 - "Frontend UI Engineering"
Cohesion: 0.08
Nodes (23): Accessibility (WCAG 2.1 AA), ARIA Labels, Avoid the AI Aesthetic, Color, Common Rationalizations, Component Architecture, Component Patterns, Design System Adherence (+15 more)

### Community 47 - "Context Engineering"
Cohesion: 0.09
Nodes (22): Anti-Patterns, Common Rationalizations, Confusion Management, Context Engineering, Context Packing Strategies, Level 1: Rules Files, Level 2: Specs and Architecture, Level 3: Relevant Source Files (+14 more)

### Community 48 - "Incremental Implementation"
Cohesion: 0.09
Nodes (22): Common Rationalizations, Contract-First Slicing, Implementation Rules, Increment Checklist, Incremental Implementation, Overview, Red Flags, Risk-First Slicing (+14 more)

### Community 49 - "Code Simplification"
Cohesion: 0.09
Nodes (21): 1. Preserve Behavior Exactly, 2. Follow Project Conventions, 3. Prefer Clarity Over Cleverness, 4. Maintain Balance, 5. Scope to What Changed, Code Simplification, Common Rationalizations, Language-Specific Guidance (+13 more)

### Community 50 - "Debugging and Error Recovery"
Cohesion: 0.09
Nodes (21): Build Failure Triage, Common Rationalizations, Debugging and Error Recovery, Error-Specific Patterns, Instrumentation Guidelines, Overview, Red Flags, Runtime Error Triage (+13 more)

### Community 51 - "Documentation and ADRs"
Cohesion: 0.09
Nodes (21): ADR Lifecycle, ADR Template, API Documentation, Architecture Decision Records (ADRs), Changelog Maintenance, Common Rationalizations, Document Known Gotchas, Documentation and ADRs (+13 more)

### Community 52 - "Performance Optimization"
Cohesion: 0.10
Nodes (20): Common Rationalizations, Core Web Vitals Targets, Large Bundle Size, Missing Caching (Backend), Missing Image Optimization (Frontend), N+1 Queries (Backend), Overview, Performance Budget (+12 more)

### Community 53 - "ReOrder: Keep Your Regulars Ordering Direct"
Cohesion: 0.11
Nodes (17): Example 1: Vague Early-Stage Concept (Full 3-Phase Session), Example 2: Feature Idea Within an Existing Product (Codebase-Aware), Example 3: Process/Workflow Idea (Non-Product), Ideation Session Examples, Key Assumptions to Validate, MVP Scope, Not Doing (and Why), Open Questions (+9 more)

### Community 54 - "Interview Me"
Cohesion: 0.11
Nodes (17): Common Rationalizations, Example, Interaction with Other Skills, Interview Me, Loading Constraints, Output, Overview, Red Flags (+9 more)

### Community 55 - "Planning and Task Breakdown"
Cohesion: 0.11
Nodes (17): Common Rationalizations, Output Files, Overview, Parallelization Opportunities, Plan Document Template, Planning and Task Breakdown, Red Flags, See Also (+9 more)

### Community 56 - "Doubt-Driven Development"
Cohesion: 0.12
Nodes (15): Common Rationalizations, Cross-model escalation, Doubt-Driven Development, Interaction with Other Skills, Loading Constraints, Overview, Red Flags, Step 1: CLAIM — Surface what stands (+7 more)

### Community 57 - "Idea Refine"
Cohesion: 0.13
Nodes (14): Anti-patterns to Avoid, Detailed Instructions, How It Works, Idea Refine, Output, Phase 1: Understand & Expand (Divergent), Phase 2: Evaluate & Converge, Phase 3: Sharpen & Ship (+6 more)

### Community 58 - "Process"
Cohesion: 0.13
Nodes (14): 1. Define "working" before instrumenting, 2. Pick the right signal for each question, 3. Structured logging, 4. Metrics, 5. Distributed tracing, 6. Alerting, 7. Verify the telemetry itself, Common Rationalizations (+6 more)

### Community 59 - "Using Agent Skills"
Cohesion: 0.13
Nodes (14): 1. Surface Assumptions, 2. Manage Confusion Actively, 3. Push Back When Warranted, 4. Enforce Simplicity, 5. Maintain Scope Discipline, 6. Verify, Don't Assume, Core Operating Behaviors, Failure Modes to Avoid (+6 more)

### Community 60 - "Spec-Driven Development"
Cohesion: 0.15
Nodes (12): Common Rationalizations, Keeping the Spec Alive, Overview, Phase 1: Specify, Phase 2: Plan, Phase 3: Tasks, Phase 4: Implement, Red Flags (+4 more)

### Community 61 - "Refinement & Evaluation Criteria"
Cohesion: 0.17
Nodes (11): 1. User Value, 2. Feasibility, 3. Differentiation, Assumption Audit, Core Evaluation Dimensions, Decision Framework, Might Be True (Nice to Have), Must Be True (Dealbreakers) (+3 more)

### Community 62 - "Source-Driven Development"
Cohesion: 0.17
Nodes (11): Common Rationalizations, Overview, Red Flags, Source-Driven Development, Step 1: Detect Stack and Versions, Step 2: Fetch Official Documentation, Step 3: Implement Following Documented Patterns, Step 4: Cite Your Sources (+3 more)

### Community 63 - "Spec: Welcome to the Jungle (WTTJ) Job Scraper"
Cohesion: 0.17
Nodes (11): Assumptions (confirmed with user), Boundaries, Code Style, Commands, Objective, Open Questions, Project Structure, Spec: Welcome to the Jungle (WTTJ) Job Scraper (+3 more)

### Community 64 - "Ideation Frameworks Reference"
Cohesion: 0.22
Nodes (8): Analogous Inspiration, Constraint-Based Ideation, First Principles Thinking, How Might We (HMW), Ideation Frameworks Reference, Jobs to Be Done (JTBD), Pre-mortem, SCAMPER

### Community 65 - "_config"
Cohesion: 0.39
Nodes (8): _config(), WorkModality, test_defaults(), test_forbids_unknown_fields(), test_rejects_distance_out_of_range(), test_strips_whitespace_from_title_and_location(), test_time_posted_value_maps_every_member(), test_work_modality_value_maps_every_member()

## Knowledge Gaps
- **492 isolated node(s):** `idea-refine.sh script`, `raw_db.linkedin.raw_linkedin_jobs`, `joblytics`, `Overview`, `When to Use` (+487 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `RawJobOffer` connect `RawJobOffer` to `LinkedInConfig`, `.header`, `job_offer.py`, `🧑‍💻 Command Line Interface (Typer)`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `LinkedInPipeline` connect `🧑‍💻 Command Line Interface (Typer)` to `LinkedInConfig`, `NoOffersFoundError`, `Settings`, `RawJobOffer`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Why does `LinkedInClient` connect `LinkedInConfig` to `HttpPolicy`, `🧑‍💻 Command Line Interface (Typer)`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Are the 18 inferred relationships involving `RawJobOffer` (e.g. with `RawJobOfferRepository` and `SnowflakeRawJobOfferRepository`) actually correct?**
  _`RawJobOffer` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `HttpPolicy` (e.g. with `LogLevel` and `RuntimeSettings`) actually correct?**
  _`HttpPolicy` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `ScrapeClient` (e.g. with `HttpPolicy` and `RandomHeaderProvider`) actually correct?**
  _`ScrapeClient` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `LinkedInParser` (e.g. with `LinkedInPipeline` and `test_parse_job_details_extracts_description_time_and_criteria()`) actually correct?**
  _`LinkedInParser` has 10 INFERRED edges - model-reasoned connections that need verification._