import pytest
from pathlib import Path
from joblytics.core.config.settings import Settings, get_settings, LogLevel
from joblytics.core.config.logger import compute_log_file


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    settings = get_settings(
        read_env=False, PROJECT_ROOT=tmp_path, LOG_LEVEL=LogLevel.INFO
    )
    return settings


def test_resolve_log_file(tmp_path: Path) -> None:
    settings = get_settings(
        read_env=False, PROJECT_ROOT=tmp_path, LOG_LEVEL=LogLevel.INFO
    )
    settings.LOG_FILE = Path("logs/joblytics.log")
    resolved = settings.resolve_log_file()
    assert resolved.is_absolute()
    assert str(resolved).startswith(str(tmp_path))


def test_compute_log_file_verbose(tmp_path: Path):
    settings = get_settings(
        read_env=False, PROJECT_ROOT=tmp_path, LOG_LEVEL=LogLevel.INFO
    )
    p = compute_log_file(settings, verbose=True)
    assert str(p).startswith(str(tmp_path))
    assert str(p).endswith("logs/joblytics.log")


def test_snowflake_raw_target_defaults_to_linkedin_shape() -> None:
    settings = get_settings(read_env=False)

    target = settings.snowflake_raw_target("linkedin")

    assert target.table_ref == "RAW_DB.LINKEDIN.RAW_LINKEDIN_JOBS"
    assert target.stage_ref == "@RAW_DB.LINKEDIN.JOBLYTICS_RAW_STAGE"


def test_snowflake_raw_target_unknown_provider_falls_back_to_default() -> None:
    settings = get_settings(read_env=False)

    assert settings.snowflake_raw_target("unknown") == settings.snowflake_raw_target(
        "linkedin"
    )


def test_snowflake_raw_target_wttj_has_its_own_schema_and_table() -> None:
    settings = get_settings(read_env=False)

    target = settings.snowflake_raw_target("wttj")

    assert target.table_ref == "RAW_DB.WTTJ.RAW_WTTJ_JOBS"
    assert target.stage_ref == "@RAW_DB.WTTJ.JOBLYTICS_RAW_STAGE"


def test_snowflake_raw_target_default_reflects_flat_field_overrides() -> None:
    settings = get_settings(
        read_env=False,
        SNOWFLAKE_RAW_DATABASE="OTHER_DB",
        SNOWFLAKE_RAW_SCHEMA="OTHER_SCHEMA",
        SNOWFLAKE_STAGE="OTHER_STAGE",
        SNOWFLAKE_TABLE="OTHER_TABLE",
    )

    linkedin_target = settings.snowflake_raw_target("linkedin")
    wttj_target = settings.snowflake_raw_target("wttj")

    assert linkedin_target.table_ref == "OTHER_DB.OTHER_SCHEMA.OTHER_TABLE"
    # wttj keeps its own hardcoded target, unaffected by the flat overrides
    assert wttj_target.table_ref == "RAW_DB.WTTJ.RAW_WTTJ_JOBS"
