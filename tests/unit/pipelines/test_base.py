from datetime import datetime, timedelta, timezone
from typing import Sequence

import pytest
from pydantic import HttpUrl

from joblytics.domain.entities.job_offer import RawJobOffer
from joblytics.domain.repositories.raw_job_offer_repository import (
    RawJobOfferRepository,
)
from joblytics.pipelines.base import (
    BaseJobPipeline,
    PipelineReport,
    TimePosted,
    WorkModality,
)


def _offer(job_id: str) -> RawJobOffer:
    return RawJobOffer(
        provider="linkedin",
        provider_job_id=job_id,
        url=HttpUrl("https://www.linkedin.com/jobs/view/" + job_id),
        title="Data Engineer",
        company="Acme",
    )


class _FakePipeline(BaseJobPipeline):
    def __init__(
        self,
        offers: list[RawJobOffer] | None = None,
        error: Exception | None = None,
        repository: RawJobOfferRepository | None = None,
    ):
        super().__init__(
            provider="linkedin",
            title="Data Engineer",
            location="Paris",
            time_posted=TimePosted.DAY,
            work_modality=WorkModality.REMOTE,
            repository=repository,
        )
        self._offers = offers or []
        self._error = error

    def extract_jobs(self) -> list[RawJobOffer]:
        if self._error:
            raise self._error
        return self._offers


class _FakeRepository:
    def __init__(self, loaded: int | None = None, error: Exception | None = None):
        self._loaded = loaded
        self._error = error
        self.saved: list[RawJobOffer] = []

    def save_batch(self, offers: Sequence[RawJobOffer]) -> int:
        if self._error:
            raise self._error
        self.saved = list(offers)
        return self._loaded if self._loaded is not None else len(offers)


def test_pipeline_report_duration_and_human_duration() -> None:
    started = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    finished = started + timedelta(minutes=2, seconds=5)
    report = PipelineReport(
        provider="linkedin",
        produced=3,
        loaded=0,
        started_at=started,
        finished_at=finished,
    )
    assert report.duration == timedelta(minutes=2, seconds=5)
    assert report.human_duration == "2m 5s"


def test_run_success_returns_report_with_sample() -> None:
    offers = [_offer(str(i)) for i in range(7)]
    pipeline = _FakePipeline(offers=offers)

    report = pipeline.run()

    assert report.provider == "linkedin"
    assert report.produced == 7
    assert len(report.sample_data) == 5
    assert report.errors == ()


def test_run_with_no_offers_still_returns_report() -> None:
    pipeline = _FakePipeline(offers=[])

    report = pipeline.run()

    assert report.produced == 0
    assert report.sample_data == []


def test_run_propagates_exception_and_records_error() -> None:
    pipeline = _FakePipeline(error=ValueError("boom"))

    with pytest.raises(ValueError, match="boom"):
        pipeline.run()

    assert len(pipeline._errors) == 1
    assert "boom" in pipeline._errors[0]


def test_run_persists_via_repository_and_reports_loaded_count() -> None:
    offers = [_offer(str(i)) for i in range(3)]
    repository = _FakeRepository()
    pipeline = _FakePipeline(offers=offers, repository=repository)

    report = pipeline.run()

    assert report.loaded == 3
    assert repository.saved == offers
    assert report.errors == ()


def test_run_without_repository_reports_zero_loaded() -> None:
    pipeline = _FakePipeline(offers=[_offer("1")])

    report = pipeline.run()

    assert report.loaded == 0


def test_run_with_no_offers_does_not_call_repository() -> None:
    repository = _FakeRepository()
    pipeline = _FakePipeline(offers=[], repository=repository)

    report = pipeline.run()

    assert report.loaded == 0
    assert repository.saved == []


def test_run_survives_repository_failure_and_records_error() -> None:
    repository = _FakeRepository(error=RuntimeError("snowflake down"))
    pipeline = _FakePipeline(offers=[_offer("1")], repository=repository)

    report = pipeline.run()

    assert report.produced == 1
    assert report.loaded == 0
    assert any("snowflake down" in error for error in report.errors)


@pytest.mark.parametrize(
    "member,value",
    [
        (TimePosted.ALL, "all"),
        (TimePosted.DAY, "day"),
        (TimePosted.WEEK, "week"),
        (TimePosted.MONTH, "month"),
        (WorkModality.ALL, "all"),
        (WorkModality.ONSITE, "onsite"),
        (WorkModality.HYBRID, "hybrid"),
        (WorkModality.REMOTE, "remote"),
    ],
)
def test_shared_query_filter_values(member, value: str) -> None:
    assert member.value == value
