import warnings

from joblytics.core.config.raw_target import (
    SnowflakeRawTarget,
    SnowflakeRawTargetResolver,
)


def _target(**overrides: str) -> SnowflakeRawTarget:
    defaults = {
        "database": "RAW_DB",
        "schema_name": "LINKEDIN",
        "stage": "JOBLYTICS_RAW_STAGE",
        "table": "RAW_LINKEDIN_JOBS",
    }
    defaults.update(overrides)
    return SnowflakeRawTarget(**defaults)


def test_stage_ref_and_table_ref_are_fully_qualified() -> None:
    target = _target()

    assert target.stage_ref == "@RAW_DB.LINKEDIN.JOBLYTICS_RAW_STAGE"
    assert target.table_ref == "RAW_DB.LINKEDIN.RAW_LINKEDIN_JOBS"


def test_for_provider_returns_default_when_no_override() -> None:
    default = _target()
    resolver = SnowflakeRawTargetResolver(default=default)

    assert resolver.for_provider("unknown") == default


def test_for_provider_returns_full_override_not_a_merge() -> None:
    default = _target()
    override = _target(
        database="RAW_DB",
        schema_name="WTTJ",
        stage="JOBLYTICS_RAW_STAGE",
        table="RAW_WTTJ_JOBS",
    )
    resolver = SnowflakeRawTargetResolver(
        default=default, per_provider={"wttj": override}
    )

    resolved = resolver.for_provider("wttj")

    assert resolved == override
    assert resolved.table_ref == "RAW_DB.WTTJ.RAW_WTTJ_JOBS"


def test_construction_raises_no_pydantic_shadow_warning() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _target()
