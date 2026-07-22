# Todo: WTTJ Scraper (extraction + Snowflake Raw layer only)

See `tasks/plan.md` for full context/rationale. dbt staging is out of
scope for this pass.

## Phase 1: Settings & Repository generalization
- [x] 1.0 Baseline: `poetry run pytest`/ruff/mypy on current `main` (make quality itself is broken by an unrelated pre-existing Makefile/.env issue, see final report)
- [x] 1.1 `src/joblytics/core/config/raw_target.py`: `SnowflakeRawTarget` + `SnowflakeRawTargetResolver`
- [x] 1.2 Wire resolver into `Settings` (sync flat fields into `default`, add `wttj` target + HTTP policy)
- [x] 1.3 Make `SnowflakeRawJobOfferRepository` provider-aware
- [x] 1.4 Fix stale-field-name bug in repository test + add resolver tests
- [x] Checkpoint: pytest/ruff/mypy green (120 passed), LinkedIn stage/table strings unchanged

## Phase 2: `pipelines/wttj/` package
- [x] 2.1 `models.py`: `WTTJConfig` + tests
- [x] 2.2 `constants.py`: sitemap URL, JSON-LD type constant
- [x] 2.3 `client.py`: `WTTJClient` + tests
- [x] 2.4 `parser.py`: sitemap/candidate/JSON-LD parsing + fixtures + tests (verified datePosted is absolute ISO-8601 across 3 real pages)
- [x] 2.5 `pipeline.py`: `WTTJPipeline` + tests
- [x] Checkpoint: 139 passed offline; no LinkedIn regression

## Phase 3: headers.py Referer handling
- [x] 3.1 Refactor to per-provider referer lookup, add `wttj` entry + tests

## Phase 4: CLI `wttj` command
- [x] 4.1 Add `wttj` Typer command
- [x] 4.2 Mirror CLI tests for `wttj`
- [x] Checkpoint: CLI test suite green (14 passed), `joblytics --help` shows both commands

## Phase 5: Snowflake Raw layer DDL (no dbt models)
- [x] 5.1 `dbt_project/analyses/setup/raw_wttj_jobs.sql` (manual Snowflake worksheet run still needed by user)

## Phase 6: Full regression rollup
- [x] 6.1 ruff format/fix + mypy + pytest --cov (Makefile's actual steps, run via poetry directly since `make quality` itself is broken — see final report). 151 passed, 99.24% coverage, 100% on all new wttj code.
- [x] Live smoke test: sitemap+shard+candidate-filtering proven against the real site (38 real candidates found); detail-page JSON-LD parsing proven against 3 real captured pages; live end-to-end detail fetch hit WAF challenges this session (likely IP burst from research+testing) but pipeline degraded gracefully (skip+continue, no crash) exactly as designed.
