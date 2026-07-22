# Implementation Plan: Welcome to the Jungle (WTTJ) Job Scraper

## Context

`specs/wttj-scraper.md` already defines the goal: add a `wttj` scraping
pipeline mirroring the existing LinkedIn pipeline's architecture, landing
raw offers in their own Snowflake schema, staged by dbt alongside LinkedIn.

During planning, live (read-only) probing of the real
welcometothejungle.com site was performed to validate the spec's riskiest
assumption (that WTTJ could be scraped the same way as LinkedIn — search
HTML + CSS selectors). That assumption was **partially refuted**:

- **Search/listing pages are pure client-side rendered** (Next.js App
  Router) — the raw HTML contains no job data and doesn't reflect query
  params server-side. There's no LinkedIn-equivalent "scrape search HTML,
  paginate" step available over plain HTTP.
- `robots.txt` explicitly **disallows** `*/jobs?query=*` (any query-string
  search URL) — so this isn't just a technical gap, it's also a compliance
  boundary this project should respect (per the project's own "engineering
  responsibility" standard for scraping).
- **Individual job detail pages are server-rendered** and expose a
  standard `schema.org/JobPosting` JSON-LD block — title, company,
  location, description, and `datePosted` as an **absolute ISO-8601
  timestamp** (not LinkedIn-style relative text). This is more reliable
  than LinkedIn's CSS-selector criteria walking.
- A public, robots-allowed **sitemap** (`sitemaps/index.xml.gz` →
  `job-listings.N.xml.gz` shards) lists all live job detail URLs — usable
  for discovery, but unfiltered (no title/location search), so
  title/location filtering has to happen client-side against URL slugs.
- An **AWS WAF Bot Control** challenge intermittently blocks requests
  depending on User-Agent fingerprint — needs a more conservative rate
  limit than LinkedIn's policy.

Presented with these findings, the user chose the **sitemap enumeration +
client-side slug filtering** discovery strategy: no new dependency,
robots.txt-compliant, at the cost of weaker filter precision/recall than a
real search (documented limitation, not a silent one). This plan is built
around that choice.

**Scope for this implementation**: extraction + load into the Snowflake
Raw (Bronze) layer only — i.e. everything up through
`RAW_DB.WTTJ.RAW_WTTJ_JOBS` being populated. dbt staging models,
`sources.yml`/`schema.yml`, and any transformation logic are explicitly
**out of scope** for this pass and deferred to a follow-up plan, mirroring
how `dbt_project/models/01_staging/linkedin/` would be a separate,
subsequent effort if it didn't already exist.

## Architecture Decisions

- **Discovery**: enumerate job URLs via WTTJ's public sitemap, filter
  candidates in-Python by matching title/location tokens against the URL
  slug. Best-effort, not a real filtered search — documented as such.
- **Detail enrichment**: parse the `schema.org/JobPosting` JSON-LD block
  from each candidate detail page (BeautifulSoup locates the
  `<script type="application/ld+json">` tag, `json.loads` parses it) —
  no CSS-selector guessing needed, unlike LinkedIn's parser.
- **Settings/Repository generalization**: replace the flat
  `SNOWFLAKE_RAW_SCHEMA`/`SNOWFLAKE_STAGE`/`SNOWFLAKE_TABLE` globals with a
  per-provider `SnowflakeRawTargetResolver` (mirrors the existing
  `HttpPolicy`/`PolicyResolver` shape in
  `src/joblytics/core/config/policy.py`), using **full-replacement**
  semantics per provider (never a partial merge) — a forgotten override
  field must not silently misroute one provider's data into another's
  table. LinkedIn's existing flat env vars keep working unchanged via a
  `model_validator` that syncs them into the resolver's `default`.
- **HTTP policy for `wttj`**: more conservative than LinkedIn's (lower
  rate, wider jitter, fewer parallel workers) given the WAF finding.
- **Referer handling**: light refactor of `headers.py`'s single inline
  LinkedIn `if` branch into a small per-provider lookup table — cheap to
  do now, avoids stacking a second inline branch that becomes unreadable
  at provider #3.

## Task List

### Phase 1: Settings & Repository generalization (foundation — start first; independent of Phase 2)

- **Task 1.0 — Baseline**: run `make quality` on current `main` to capture
  today's LinkedIn-only pass/coverage baseline, before touching any shared
  code.
- **Task 1.1 — New resolver model**: `src/joblytics/core/config/raw_target.py`
  — `SnowflakeRawTarget` (fields: `database`, `schema_name` — **not**
  `schema`, which Pydantic v2 warns/shadows on `BaseModel` — `stage`,
  `table`; computed `stage_ref`/`table_ref` properties) and
  `SnowflakeRawTargetResolver` (`default: SnowflakeRawTarget`,
  `per_provider: dict[str, SnowflakeRawTarget]`, `for_provider()` returns
  the full override or the full default — never merges partial fields).
- **Task 1.2 — Wire into `Settings`**
  (`src/joblytics/core/config/settings.py`): add `SNOWFLAKE_RAW_TARGETS`
  defaulting to today's LinkedIn values, plus a `"wttj"` entry
  (`database="RAW_DB"`, `schema_name="WTTJ"`, `stage="JOBLYTICS_RAW_STAGE"`,
  `table="RAW_WTTJ_JOBS"`); add a `model_validator(mode="after")` that syncs
  the existing flat `SNOWFLAKE_RAW_DATABASE`/`SCHEMA`/`STAGE`/`TABLE` fields
  into the resolver's `default` (preserves current env-var behavior for
  LinkedIn exactly); add a `snowflake_raw_target(provider)` helper
  (mirrors the existing `http_policy(provider)` method); add a `"wttj"`
  entry to `HTTP_POLICIES.per_provider` with a conservative rate limit
  (tune exact numbers during implementation, not guessed here).
- **Task 1.3 — Provider-aware repository**:
  `src/joblytics/infrastructure/repositories/snowflake_raw_job_offer_repository.py`
  — replace the four flat-settings reads with
  `self._settings.snowflake_raw_target(offers[0].provider)`, use
  `target.database` / `target.schema_name` / `target.stage_ref` /
  `target.table_ref`. No constructor or CLI-level change required —
  `SnowflakeRawJobOfferRepository(get_settings())` stays identical for both
  providers.
- **Task 1.4 — Fix existing test bug + add resolver tests**: the current
  `_settings()` helper in
  `tests/unit/infrastructure/repositories/test_snowflake_raw_job_offer_repository.py`
  passes `SNOWFLAKE_DATABASE=`/`SNOWFLAKE_SCHEMA=` kwargs that **don't
  exist** as `Settings` fields (real names are `SNOWFLAKE_RAW_DATABASE`/
  `SNOWFLAKE_RAW_SCHEMA`) — silently dropped by Pydantic's default
  `extra="ignore"`, so the test currently only passes because the class
  defaults happen to match. Fix the field names and add an assertion that
  an override actually changes the resolved output (proving it's live, not
  coincidental). Add new tests to `tests/unit/core/test_settings.py`
  covering `snowflake_raw_target()` for `linkedin`, an unknown provider,
  and `wttj`; add a WTTJ-flavored batch test to the repository test file
  asserting resolution to `RAW_DB.WTTJ.*`.
- **Checkpoint**: `make quality` green; LinkedIn's resolved
  stage/table strings unchanged (`RAW_DB.LINKEDIN.RAW_LINKEDIN_JOBS`,
  `@RAW_DB.LINKEDIN.JOBLYTICS_RAW_STAGE`); new WTTJ resolver tests pass.

### Phase 2: `pipelines/wttj/` package (depends on the discovery-strategy decision, already made)

- **Task 2.1 — `models.py`**: `WTTJConfig`, mirroring
  `pipelines/linkedin/models.py`'s `LinkedInConfig` (title/location
  validated + stripped, `time_posted`/`work_modality` enums,
  `extra="forbid"`). Since discovery is sitemap-based (no filtered search
  endpoint to map onto), `time_posted_value`/`work_modality_value` become
  **local filter predicates** applied after JSON-LD parsing rather than URL
  query values — document this divergence clearly in the docstring, it's
  intentional, not an oversight. Tests:
  `tests/unit/pipelines/wttj/test_models.py`, mirroring
  `tests/unit/pipelines/linkedin/test_models.py`.
- **Task 2.2 — `constants.py`**: `WTTJ_SITEMAP_INDEX_URL =
  "https://www.welcometothejungle.com/sitemaps/index.xml.gz"`, a shard-name
  filter (`job-listings`), `JOB_POSTING_LD_TYPE = "JobPosting"`. No CSS
  selector dicts — detail data comes from JSON-LD, not DOM walking; note
  this explicitly in the module docstring since it's a deliberate departure
  from `pipelines/linkedin/constants.py`'s shape.
- **Task 2.3 — `client.py`**: `WTTJClient` wraps the shared `ScrapeClient`
  (`src/joblytics/infrastructure/http/scraping/http_client.py`) exactly
  like `LinkedInClient`. `build_sitemap_index_url()`, `request(url)`
  delegating to `scrape_client.web_page_search`. Confirm during
  implementation whether sitemap shards need explicit
  `gzip.decompress(response.content)` (the `.gz` file extension likely
  isn't auto-decoded via `Content-Encoding`, unlike `requests`' transparent
  gzip transfer-encoding handling). Tests mirror
  `tests/unit/pipelines/linkedin/test_client.py`'s URL-building style.
- **Task 2.4 — `parser.py`**: pure text/bytes-in, no network calls
  (mirrors `LinkedInParser`'s boundary):
  - `parse_sitemap_index(xml_bytes) -> list[str]` — shard URLs.
  - `parse_job_listing_urls(xml_bytes) -> list[str]` — `<loc>` values.
  - `filter_candidate_urls(urls, title, location) -> list[str]` —
    best-effort, case/accent-insensitive slug substring matching;
    docstring must state plainly this is not a real filtered search.
  - `parse_job_detail(html) -> dict[str, Any]` — locate
    `<script type="application/ld+json">` blocks, `json.loads`, select the
    one with `"@type": "JobPosting"`, map into the same dict shape
    `LinkedInParser.parse_job_details` returns (`description`,
    `raw_description_html`, `raw_contract_type`, `raw_time_posted` as the
    ISO string, `raw_seniority` if derivable).
  - Tests use small, hand-trimmed fixture files under
    `tests/unit/pipelines/wttj/fixtures/` (a JSON-LD block, a couple of
    sitemap `<loc>` entries) — fully offline, no live network calls from
    the test suite, matching this repo's existing "unit tests only"
    convention.
  - Before finalizing, re-verify the `datePosted` ISO-8601 format against
    2-3 more real detail pages (only one was sampled during planning).
- **Task 2.5 — `pipeline.py`**: `WTTJPipeline(BaseJobPipeline)`.
  `extract_jobs()`: (1) fetch sitemap index, filter `job-listings.*`
  shards; (2) fetch shard(s) with an explicit cap on shards-scanned per
  query (bounds latency — size and document the cap); (3)
  `filter_candidate_urls` → if empty, raise `NoOffersFoundError` (same
  exception/signature as LinkedIn's); (4) flip
  `client.scrape_client.enable_throttle = True` before the heavy phase
  (mirrors LinkedIn); (5) `ThreadPoolExecutor(max_workers=3)` (tighter than
  LinkedIn's 5, given WAF sensitivity) fetches+parses each candidate,
  merges `provider`/`search_*` echo fields into `RawJobOffer`; per-candidate
  failures are logged and dropped, not fatal. Docstring must note the
  structural difference from LinkedIn: no separate cheap-summary step —
  each candidate requires exactly one fetch since JSON-LD already has full
  data. Tests mirror `tests/unit/pipelines/linkedin/test_pipeline.py`'s
  `_FakeClient`/`_FakeParser` monkeypatch style (no `requests-mock`):
  happy path, zero-candidates → `NoOffersFoundError`, per-candidate fetch
  failure dropped, non-`JobPosting` JSON-LD dropped gracefully.
- **Checkpoint**: `pytest tests/unit/pipelines/wttj/ -v` green, fully
  offline; no regression in `tests/unit/pipelines/linkedin/`.

### Phase 3: `headers.py` Referer handling

- **Task 3.1**: refactor `RandomHeaderProvider.header()` in
  `src/joblytics/infrastructure/http/scraping/headers.py` from the single
  inline LinkedIn `if` branch into a small
  `_PROVIDER_REFERER_RULES: dict[str, list[tuple[str, str]]]` lookup
  (path-substring → Referer value, per provider), with a `wttj` entry sized
  once Phase 2's real URL shapes exist. LinkedIn's existing behavior must
  stay byte-identical (same header values for the same URLs) before/after.
  Add/extend a `tests/unit/infrastructure/http/scraping/test_headers.py`
  covering both providers plus the "neither matches → no Referer key" case.

### Phase 4: CLI `wttj` command

- **Task 4.1**: add a `wttj` Typer command to `src/joblytics/cli.py`,
  copying the `linkedin` command's shape verbatim — same args/options
  (`title`, `location`, `time_posted`, `work_modality`, `--show-table`,
  `--dry-run`), same `NoOffersFoundError`→exit 0 / generic `Exception`→exit
  1 handling, same `render_table` call (`src/joblytics/core/utils/cli.py`)
  with identical `drop`/`col_limits`.
  `SnowflakeRawJobOfferRepository(get_settings())` construction is
  **unchanged** — no provider-awareness needed at the CLI layer, that's
  fully resolved inside the repository from Phase 1.
- **Task 4.2**: mirror every existing `test_linkedin_command_*` test in
  `tests/unit/test_cli.py` for `wttj` (success, no-offers, unexpected
  error, show-table, no-show-table-by-default, dry-run-skips-repository,
  without-dry-run-builds-repository).
- **Checkpoint**: full CLI test suite green; `joblytics --help` lists both
  `linkedin` and `wttj`.

### Phase 5: Snowflake Raw (Bronze) layer setup — DDL only, no dbt models

- **Task 5.1**: `dbt_project/analyses/setup/raw_wttj_jobs.sql` — copy
  `raw_linkedin_jobs.sql` structurally, swap `linkedin`→`wttj` literals
  (`RAW_DB.WTTJ`, stage `JOBLYTICS_RAW_STAGE`, table `RAW_WTTJ_JOBS`,
  same 2-column shape: `src_json variant, _loaded_at timestamp_ltz default
  current_timestamp()`), matching Task 1.2's resolver values exactly. This
  is a manual, one-time DDL script (not run by dbt or the app), same as
  the LinkedIn one — it only needs to exist so the raw table is ready to
  receive data from `SnowflakeRawJobOfferRepository`.
- **Out of scope for this plan** (explicitly deferred): dbt staging models,
  `sources.yml`/`schema.yml`, and any relative-time-parsing logic for WTTJ.
  These would live under `dbt_project/models/01_staging/wttj/` in a future
  follow-up plan, mirroring `dbt_project/models/01_staging/linkedin/`.
- **Checkpoint**: manually running `raw_wttj_jobs.sql` in a Snowflake
  worksheet creates `RAW_DB.WTTJ.RAW_WTTJ_JOBS` with the expected 2-column
  shape; no dbt build/test is part of this phase.

### Phase 6: Full regression rollup

- **Task 6.1**: `make fmt && make quality` across the whole repo; diff
  against Phase 1's baseline to confirm zero LinkedIn regressions; confirm
  the extraction+raw-load success criteria (see Verification below) are
  met. dbt-related success criteria from `specs/wttj-scraper.md` are
  **not** in scope for this rollup — they apply to the deferred staging
  follow-up.

## Dependency Order

Phase 1 and the (already-completed) discovery-strategy research can run
independently/first. Phase 2 depends on the discovery decision (resolved).
Phase 3 depends on Phase 2 (needs real WTTJ URL shapes). Phase 4 depends on
Phase 1 + Phase 2. Phase 5 depends only on Phase 1 (target names) and can
be drafted in parallel with Phase 2/3. Phase 6 depends on all prior
phases.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Sitemap slug-filtering has weak precision/recall vs. a real search | Documented limitation, not hidden; cap shards scanned per query to bound latency |
| AWS WAF Bot Control may still challenge/block requests | Conservative `wttj` `HttpPolicy` (lower rate, wider jitter, fewer parallel workers than LinkedIn); per-candidate failures don't kill the whole run |
| Settings/Repository generalization regresses LinkedIn's Snowflake loading | Baseline `make quality` run before edits; resolver uses full-replacement semantics (never merges), so LinkedIn's resolved target is unchanged unless flat env vars are explicitly changed; explicit regression tests |
| Pydantic v2 shadows `BaseModel` if a field is literally named `schema` | Use `schema_name` field name (confirmed via live construction check during planning) |
| Stale `SNOWFLAKE_DATABASE`/`SNOWFLAKE_SCHEMA` kwargs already silently ignored in the existing repository test | Fixed in Task 1.4, with an assertion proving the override is live, not coincidental |
| `datePosted`/JSON-LD assumptions based on a single sampled job posting | Re-verify against 2-3 more real detail pages during Task 2.4; exact downstream parsing (e.g. relative-time handling) is deferred to the dbt staging follow-up, so this only affects `raw_time_posted`'s raw string capture for now |

## Verification

- `make quality` (ruff, mypy strict, pytest+coverage) green at each phase
  checkpoint, zero regressions on existing LinkedIn tests/coverage
  threshold.
- `pytest tests/unit/pipelines/wttj/ tests/unit/test_cli.py
  tests/unit/core/test_settings.py tests/unit/infrastructure/ -v` all
  green, fully offline (no live network calls from the test suite itself).
- Manual smoke test: `joblytics wttj "Data Engineer" "Paris" --dry-run -v
  --show-table` runs end-to-end against the live site and prints a
  non-empty results table (validates the real sitemap + JSON-LD parsing
  path); repeat without `--dry-run` against a test/dev Snowflake target to
  confirm rows land in `RAW_DB.WTTJ.RAW_WTTJ_JOBS` without touching
  `RAW_DB.LINKEDIN.RAW_LINKEDIN_JOBS`.
- `joblytics --help` shows both `linkedin` and `wttj` subcommands.
- dbt staging/build verification is **not** part of this plan's scope —
  deferred to the follow-up plan covering `01_staging/wttj/`.
