# Spec: Welcome to the Jungle (WTTJ) Job Scraper

## Objective

Add a new ingestion pipeline that scrapes job postings from Welcome to the
Jungle (welcometothejungle.com), mirroring the existing LinkedIn pipeline's
architecture, so that WTTJ raw job offers land in a dedicated Snowflake
Bronze schema and can be modeled by dbt alongside LinkedIn data.

- **User**: Samir (data engineer), operating the tool via CLI.
- **Success looks like**: `joblytics wttj "Data Engineer" "Paris"` produces
  summary + detail-enriched `RawJobOffer` records, persists them to
  `RAW_DB.WTTJ.RAW_WTTJ_JOBS` (or a dry-run console table), and a
  `stg_wttj_jobs` dbt staging model cleanly parses/deduplicates them by
  `provider_job_id`, without touching or regressing the existing LinkedIn
  pipeline.

## Assumptions (confirmed with user)

1. **Scraping technique**: HTML + BeautifulSoup, mirroring LinkedIn's parser
   approach (server-rendered CSS-selector scraping). A live check of
   welcometothejungle.com's search page during spec research showed
   indicators of client-side rendering (Next.js SPA) with no job data visible
   in the raw HTML fetched — this is a **known, accepted risk**. The user
   chose to proceed on the HTML-scraping assumption rather than run a
   research spike first. The first implementation task must validate real
   page structure against actual CSS selectors and surface immediately if
   the assumption doesn't hold (see Open Questions / Boundaries) rather than
   pushing forward with guessed selectors.
2. **Snowflake landing**: a separate schema/stage/table per provider —
   `RAW_DB.WTTJ.RAW_WTTJ_JOBS` (own stage + file format), analogous to
   `RAW_DB.LINKEDIN.RAW_LINKEDIN_JOBS`. This requires generalizing `Settings`
   and `SnowflakeRawJobOfferRepository` from flat
   `SNOWFLAKE_RAW_SCHEMA`/`SNOWFLAKE_STAGE`/`SNOWFLAKE_TABLE` globals to a
   per-provider resolver (same shape as the existing
   `HTTP_POLICIES.per_provider` / `PolicyResolver` pattern).
3. **v1 scope**: full feature parity with the LinkedIn pipeline — summary
   search + pagination + parallel per-offer detail enrichment (description,
   contract type, seniority, time posted).
4. **Geography**: WTTJ operates primarily in France/Europe; query parameter
   names/values will follow whatever WTTJ's own search UI actually uses
   (likely French-language filter values) — to be confirmed once real
   page/API structure is inspected during implementation.
5. All existing generic abstractions are reused unmodified: domain entities
   (`RawJobOffer`, `NormalizedJobOffer`, enums), `BaseJobPipeline`,
   `ScrapeClient`, `HttpPolicy`/`PolicyResolver`, `RawJobOfferRepository`
   protocol. Only the WTTJ-provider-specific packages and the two
   generalizations from (2) are new/changed.
6. `RandomHeaderProvider.header()` currently hardcodes a LinkedIn-specific
   Referer branch (`if "linkedin" in str(url)`). WTTJ will need an analogous
   branch, or this gets refactored into a per-provider referer map — exact
   approach to be sized in the Plan phase.

## Tech Stack

Unchanged, fully reused: Python 3.12, Pydantic v2 / pydantic-settings, Typer,
BeautifulSoup4, `requests`, `snowflake-connector-python`, dbt-core /
dbt-snowflake, Poetry. No new dependency is expected unless assumption #1
turns out to be wrong (see Open Questions) and a headless-browser/API client
becomes necessary — that would be a scope change requiring sign-off first.

## Commands

```
Build/format:  make fmt
Quality gate:  make quality
Tests:         make test
Run scraper:   joblytics wttj "Data Engineer" "Paris" -v --show-table
Dry run:       joblytics wttj "Data Engineer" "Paris" --dry-run
dbt build:     dbt build -s stg_wttj_jobs --project-dir dbt_project --profiles-dir .
```

## Project Structure

```
src/joblytics/pipelines/wttj/
    __init__.py
    models.py       # WTTJConfig (mirrors LinkedInConfig: title/location/filters + provider-value mapping properties)
    constants.py    # base URLs, mapping dicts, CSS selectors (or JSON keys, pending assumption #1 validation)
    client.py       # WTTJClient (wraps the shared ScrapeClient)
    parser.py       # WTTJParser (BeautifulSoup, per assumption #1; no network calls)
    pipeline.py     # WTTJPipeline(BaseJobPipeline) — discovery -> summaries -> parallel enrichment

tests/unit/pipelines/wttj/
    test_models.py
    test_client.py
    test_parser.py
    test_pipeline.py

src/joblytics/cli.py                                        # + `wttj` Typer command
src/joblytics/core/config/settings.py                        # generalize raw schema/stage/table per provider; add "wttj" HTTP_POLICIES entry
src/joblytics/infrastructure/http/scraping/headers.py        # + WTTJ referer handling
src/joblytics/infrastructure/repositories/snowflake_raw_job_offer_repository.py  # read provider-scoped schema/stage/table
tests/unit/test_cli.py                                       # + wttj command tests
tests/unit/core/test_settings.py                             # + per-provider raw-target resolution tests

dbt_project/analyses/setup/raw_wttj_jobs.sql       # one-time DDL for RAW_DB.WTTJ.*
dbt_project/models/01_staging/wttj/
    sources.yml
    schema.yml
    stg_wttj_jobs.sql
dbt_project/macros/parse_wttj_relative_time.sql    # only if WTTJ exposes relative "time ago" text; skip if it gives ISO timestamps
```

## Code Style

Mirror `pipelines/linkedin/*` module-for-module: same boundaries
(models/constants/client/parser/pipeline), same Google-style docstrings
(per project `CLAUDE.md`), same Pydantic config (`extra="forbid"`), same
enum-to-provider-value property pattern in `models.py`:

```python
@property
def time_posted_value(self) -> str:
    """Map the Enum to the value that WTTJ's URL understands."""
    mapping = {...}
    return mapping[self.time_posted]
```

SQL: lowercase keywords, trailing commas, CTEs — `stg_wttj_jobs.sql` should
follow `stg_linkedin_jobs.sql`'s structure (source -> renamed -> deduplicated
CTEs) as closely as WTTJ's actual raw payload allows.

## Testing Strategy

Unit tests only, matching current repo convention (no integration tests
exist yet — `tests/integration/` is an empty placeholder). Use
monkeypatch-based fakes for pipeline orchestration tests (mirror
`test_pipeline.py`'s `_FakeClient`/`_FakeParser` pattern), not
`requests-mock`, for consistency with the existing LinkedIn suite. Parser
tests need raw HTML fixtures captured from real WTTJ pages — these can only
be written once assumption #1 is validated against the live site. Coverage
enforced via `make quality` (pytest-cov), same thresholds as the existing
suite; no regression allowed on existing LinkedIn tests.

## Boundaries

- **Always do**: define a conservative `HttpPolicy` entry for `"wttj"` in
  settings (rate limit + jitter, same spirit as LinkedIn's 0.5 req/s);
  support `--dry-run`; validate all scraped data into `RawJobOffer` before
  persisting; keep `parser.py` free of network calls.
- **Ask first**: any change that increases scraping aggressiveness relative
  to LinkedIn's policy (disabling throttle, adding proxies, a headless
  browser); the Settings/repository generalization, since it touches the
  shared code path LinkedIn already depends on — must not break
  `RAW_DB.LINKEDIN.RAW_LINKEDIN_JOBS` loading; any pivot away from the
  HTML-scraping assumption once real page structure is inspected (e.g. if
  only an internal API or headless browser turns out to work) — that's a
  new dependency and architecture change, not a like-for-like port.
- **Never do**: hardcode Snowflake credentials; commit `.env`; scrape without
  throttle/backoff; silently swallow `NoOffersFoundError`/error-handling
  conventions used by the LinkedIn pipeline.

## Success Criteria

- `joblytics wttj <title> <location>` runs end-to-end against the live site
  and returns a `PipelineReport` with `produced > 0` for a known-good query
  (manual smoke test).
- `--dry-run` skips Snowflake writes; without it, rows land in
  `RAW_DB.WTTJ.RAW_WTTJ_JOBS` and existing
  `RAW_DB.LINKEDIN.RAW_LINKEDIN_JOBS` loading is unaffected (explicit
  regression check on the Settings/repository generalization).
- `dbt build -s stg_wttj_jobs` runs clean, with `not_null`/`unique` tests
  passing on `provider_job_id`.
- New `tests/unit/pipelines/wttj/*` and CLI tests pass; full `make quality`
  (ruff, mypy, pytest+coverage) passes with zero regressions on existing
  LinkedIn tests.
- `NoOffersFoundError` is raised correctly for a query with 0 WTTJ results,
  mirroring LinkedIn's behavior.

## Open Questions

1. Real WTTJ page/API structure is unverified (assumption #1's known risk).
   The first implementation task should be a quick manual inspection
   (view-source / browser network tab against a live search URL) to confirm
   or refute HTML-scraping viability before the parser is built against
   guessed selectors.
2. Exact WTTJ query parameter names/values (title, location, contract type,
   remote modality) are unknown — to be confirmed during implementation once
   real search URLs are inspected.
3. `RandomHeaderProvider`'s inline LinkedIn-specific Referer branch: extend
   with an inline WTTJ branch (minimal diff, keeps the tech debt) or refactor
   now into a per-provider referer map (cleaner, slightly larger diff)?
   Deferred to Plan-phase sizing.
4. Pre-existing inconsistency (out of scope for this feature, flagged only):
   `dbt_project/models/01_staging/linkedin/sources.yml` documents
   `file_name`/`extracted_at` columns that don't match the raw DDL's actual
   columns (`src_json`, `_loaded_at`). WTTJ's `sources.yml` should mirror
   whichever is actually correct in Snowflake, not propagate the mismatch —
   worth a quick check against the real table before writing WTTJ's source
   definition.
