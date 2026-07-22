import gzip
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import HttpUrl

from joblytics.core.config.settings import get_settings
from joblytics.domain.entities.job_offer import RawJobOffer
from joblytics.infrastructure.repositories.errors import SnowflakeLoadError
from joblytics.infrastructure.repositories.snowflake_raw_job_offer_repository import (
    SnowflakeRawJobOfferRepository,
)


def _offer(job_id: str, provider: str = "linkedin") -> RawJobOffer:
    url = {
        "linkedin": "https://www.linkedin.com/jobs/view/",
        "wttj": "https://www.welcometothejungle.com/en/companies/acme/jobs/",
    }[provider]
    return RawJobOffer(
        provider=provider,
        provider_job_id=job_id,
        url=HttpUrl(url + job_id),
        title="Data Engineer",
        company="Acme",
    )


class _FakeCursor:
    def __init__(
        self, dict_mode: bool, sql_calls: list[str], rows: list[dict[str, Any]]
    ):
        self.dict_mode = dict_mode
        self._sql_calls = sql_calls
        self._rows = rows

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def execute(self, sql: str) -> None:
        self._sql_calls.append(sql)

    def fetchall(self) -> list[dict[str, Any]]:
        return self._rows if self.dict_mode else []


class _FakeConnection:
    def __init__(self, sql_calls: list[str], rows: list[dict[str, Any]]):
        self._sql_calls = sql_calls
        self._rows = rows

    def __enter__(self) -> "_FakeConnection":
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def cursor(self, cursor_class: object = None) -> _FakeCursor:
        return _FakeCursor(cursor_class is not None, self._sql_calls, self._rows)


def _settings():
    return get_settings(
        read_env=False,
        SNOWFLAKE_ACCOUNT="acc",
        SNOWFLAKE_USER="user",
        SNOWFLAKE_PASSWORD="pwd",
        SNOWFLAKE_ROLE="role",
        SNOWFLAKE_WAREHOUSE="wh",
        SNOWFLAKE_RAW_DATABASE="RAW_DB",
        SNOWFLAKE_RAW_SCHEMA="LINKEDIN",
        SNOWFLAKE_STAGE="JOBLYTICS_RAW_STAGE",
        SNOWFLAKE_TABLE="RAW_LINKEDIN_JOBS",
    )


def test_save_batch_empty_offers_skips_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connect_calls: list[dict[str, Any]] = []

    def fake_connect(**kwargs: Any) -> _FakeConnection:
        connect_calls.append(kwargs)
        return _FakeConnection([], [])

    monkeypatch.setattr("snowflake.connector.connect", fake_connect)

    repository = SnowflakeRawJobOfferRepository(_settings())

    assert repository.save_batch([]) == 0
    assert connect_calls == []


def test_save_batch_puts_and_copies_into_raw_table(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))

    connect_calls: list[dict[str, Any]] = []
    sql_calls: list[str] = []
    rows = [{"rows_loaded": 2}]

    def fake_connect(**kwargs: Any) -> _FakeConnection:
        connect_calls.append(kwargs)
        return _FakeConnection(sql_calls, rows)

    monkeypatch.setattr("snowflake.connector.connect", fake_connect)

    repository = SnowflakeRawJobOfferRepository(_settings())
    offers = [_offer("1"), _offer("2")]

    loaded = repository.save_batch(offers)

    assert loaded == 2
    assert connect_calls == [
        {
            "account": "acc",
            "user": "user",
            "password": "pwd",
            "role": "role",
            "warehouse": "wh",
            "database": "RAW_DB",
            "schema": "LINKEDIN",
        }
    ]
    assert any(sql.startswith("put file://") for sql in sql_calls)
    assert any(
        "copy into RAW_DB.LINKEDIN.RAW_LINKEDIN_JOBS" in sql for sql in sql_calls
    )
    assert any("@RAW_DB.LINKEDIN.JOBLYTICS_RAW_STAGE" in sql for sql in sql_calls)
    # temp file is cleaned up after the batch is loaded
    assert list(tmp_path.glob("*.json.gz")) == []


def test_write_ndjson_gzip_produces_one_json_line_per_offer(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
    repository = SnowflakeRawJobOfferRepository(_settings())
    offers = [_offer("1"), _offer("2")]

    path = repository._write_ndjson_gzip(offers)

    assert path.parent == tmp_path
    assert path.name.startswith("linkedin_")
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        lines = [json.loads(line) for line in fh]
    assert [line["provider_job_id"] for line in lines] == ["1", "2"]
    path.unlink()


def test_save_batch_uses_overridden_raw_target(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Proves the SNOWFLAKE_RAW_* overrides are actually live, not just
    coincidentally matching the class defaults."""
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))

    sql_calls: list[str] = []

    def fake_connect(**kwargs: Any) -> _FakeConnection:
        return _FakeConnection(sql_calls, [{"rows_loaded": 1}])

    monkeypatch.setattr("snowflake.connector.connect", fake_connect)

    settings = get_settings(
        read_env=False,
        SNOWFLAKE_ACCOUNT="acc",
        SNOWFLAKE_USER="user",
        SNOWFLAKE_PASSWORD="pwd",
        SNOWFLAKE_ROLE="role",
        SNOWFLAKE_WAREHOUSE="wh",
        SNOWFLAKE_RAW_DATABASE="OTHER_DB",
        SNOWFLAKE_RAW_SCHEMA="OTHER_SCHEMA",
        SNOWFLAKE_STAGE="OTHER_STAGE",
        SNOWFLAKE_TABLE="OTHER_TABLE",
    )
    repository = SnowflakeRawJobOfferRepository(settings)

    repository.save_batch([_offer("1")])

    assert any(
        "copy into OTHER_DB.OTHER_SCHEMA.OTHER_TABLE" in sql for sql in sql_calls
    )
    assert any("@OTHER_DB.OTHER_SCHEMA.OTHER_STAGE" in sql for sql in sql_calls)


def test_save_batch_routes_wttj_offers_to_their_own_target(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))

    sql_calls: list[str] = []
    connect_calls: list[dict[str, Any]] = []

    def fake_connect(**kwargs: Any) -> _FakeConnection:
        connect_calls.append(kwargs)
        return _FakeConnection(sql_calls, [{"rows_loaded": 1}])

    monkeypatch.setattr("snowflake.connector.connect", fake_connect)

    repository = SnowflakeRawJobOfferRepository(_settings())

    repository.save_batch([_offer("1", provider="wttj")])

    assert connect_calls[0]["database"] == "RAW_DB"
    assert connect_calls[0]["schema"] == "WTTJ"
    assert any("copy into RAW_DB.WTTJ.RAW_WTTJ_JOBS" in sql for sql in sql_calls)
    assert any("@RAW_DB.WTTJ.JOBLYTICS_RAW_STAGE" in sql for sql in sql_calls)


def test_save_batch_wraps_connector_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_connect(**kwargs: Any) -> _FakeConnection:
        raise RuntimeError("network unreachable")

    monkeypatch.setattr("snowflake.connector.connect", fake_connect)

    repository = SnowflakeRawJobOfferRepository(_settings())

    with pytest.raises(SnowflakeLoadError) as exc_info:
        repository.save_batch([_offer("1")])

    assert exc_info.value.table == "RAW_DB.LINKEDIN.RAW_LINKEDIN_JOBS"
    assert exc_info.value.stage == "@RAW_DB.LINKEDIN.JOBLYTICS_RAW_STAGE"
