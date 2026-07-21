import types

import pytest

from joblytics.domain.exceptions.errors import NoOffersFoundError
from joblytics.pipelines.base import TimePosted, WorkModality
from joblytics.pipelines.linkedin.pipeline import LinkedInPipeline


class _FakeResponse:
    def __init__(self, text: str = "", ok: bool = True):
        self.text = text
        self.ok = ok


def _make_fake_client(
    *,
    job_count: int,
    geo_id: int | None,
    detail_responses: dict[str, _FakeResponse],
):
    class _FakeClient:
        def __init__(self, config: object, provider: str) -> None:
            self.config = config
            self.provider = provider
            self.scrape_client = types.SimpleNamespace(enable_throttle=False)

        def build_search_url(
            self, offset: int | None = None, geo_id: int | None = None
        ) -> str:
            return "initial" if offset is None else f"page:{offset}"

        def build_detail_url(self, job_id: str) -> str:
            return f"detail:{job_id}"

        def request(self, url: str) -> _FakeResponse:
            if url == "initial":
                return _FakeResponse(text="initial-html")
            if url.startswith("page:"):
                return _FakeResponse(text=url)
            if url.startswith("detail:"):
                job_id = url.split(":", 1)[1]
                return detail_responses[job_id]
            raise AssertionError(f"unexpected url requested: {url}")

    return _FakeClient


def _make_fake_parser(
    *,
    job_count: int,
    geo_id: int | None,
    pages_cards: dict[str, list[dict[str, object]]],
    details_by_id: dict[str, dict[str, object]],
):
    class _FakeParser:
        def parse_job_count(self, html: str) -> int:
            return job_count

        def parse_geo_id(self, html: str) -> int | None:
            return geo_id

        def parse_summary_cards(self, html: str) -> list[dict[str, object]]:
            return pages_cards.get(html, [])

        def parse_job_details(self, html: str) -> dict[str, object]:
            job_id = html.split(":", 1)[1]
            return details_by_id.get(job_id, {})

    return _FakeParser


def _card(job_id: str, title: str = "Data Engineer", company: str = "Acme") -> dict:
    return {
        "provider_job_id": job_id,
        "url": f"https://example.com/jobs/{job_id}",
        "title": title,
        "company": company,
        "location": "Paris",
    }


def _pipeline(
    monkeypatch: pytest.MonkeyPatch,
    *,
    job_count,
    geo_id,
    pages_cards,
    details_by_id,
    detail_responses,
):
    fake_client = _make_fake_client(
        job_count=job_count, geo_id=geo_id, detail_responses=detail_responses
    )
    fake_parser = _make_fake_parser(
        job_count=job_count,
        geo_id=geo_id,
        pages_cards=pages_cards,
        details_by_id=details_by_id,
    )
    monkeypatch.setattr(
        "joblytics.pipelines.linkedin.pipeline.LinkedInClient", fake_client
    )
    monkeypatch.setattr(
        "joblytics.pipelines.linkedin.pipeline.LinkedInParser", fake_parser
    )
    return LinkedInPipeline(
        provider="linkedin",
        title="Data Engineer",
        location="Paris",
        time_posted=TimePosted.DAY,
        work_modality=WorkModality.REMOTE,
    )


def test_extract_jobs_returns_enriched_offers(monkeypatch: pytest.MonkeyPatch) -> None:
    pipeline = _pipeline(
        monkeypatch,
        job_count=3,
        geo_id=555,
        pages_cards={"page:0": [_card("a"), _card("b")]},
        details_by_id={
            "a": {"description": "Desc A"},
            "b": {"description": "Desc B"},
        },
        detail_responses={
            "a": _FakeResponse(text="detail:a", ok=True),
            "b": _FakeResponse(text="detail:b", ok=True),
        },
    )

    offers = pipeline.extract_jobs()

    assert {o.provider_job_id for o in offers} == {"a", "b"}
    for offer in offers:
        assert offer.provider == "linkedin"
        assert offer.search_title == "Data Engineer"
        assert offer.search_location == "Paris"
        assert offer.search_work_modality == "remote"
        assert offer.search_time_posted == "day"
    descriptions = {o.provider_job_id: o.description for o in offers}
    assert descriptions == {"a": "Desc A", "b": "Desc B"}


def test_extract_jobs_raises_when_no_offers_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline = _pipeline(
        monkeypatch,
        job_count=0,
        geo_id=None,
        pages_cards={},
        details_by_id={},
        detail_responses={},
    )

    with pytest.raises(NoOffersFoundError):
        pipeline.extract_jobs()


def test_extract_jobs_raises_when_summaries_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline = _pipeline(
        monkeypatch,
        job_count=3,
        geo_id=None,
        pages_cards={"page:0": []},
        details_by_id={},
        detail_responses={},
    )

    with pytest.raises(NoOffersFoundError):
        pipeline.extract_jobs()


def test_extract_jobs_drops_offer_with_not_ok_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline = _pipeline(
        monkeypatch,
        job_count=2,
        geo_id=None,
        pages_cards={"page:0": [_card("a"), _card("b")]},
        details_by_id={"a": {"description": "Desc A"}},
        detail_responses={
            "a": _FakeResponse(text="detail:a", ok=True),
            "b": _FakeResponse(text="detail:b", ok=False),
        },
    )

    offers = pipeline.extract_jobs()

    assert {o.provider_job_id for o in offers} == {"a"}


def test_extract_jobs_drops_offer_when_detail_request_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _RaisingResponses(dict):
        def __getitem__(self, key):
            if key == "b":
                raise RuntimeError("network error")
            return super().__getitem__(key)

    detail_responses = _RaisingResponses(a=_FakeResponse(text="detail:a", ok=True))

    pipeline = _pipeline(
        monkeypatch,
        job_count=2,
        geo_id=None,
        pages_cards={"page:0": [_card("a"), _card("b")]},
        details_by_id={"a": {"description": "Desc A"}},
        detail_responses=detail_responses,
    )

    offers = pipeline.extract_jobs()

    assert {o.provider_job_id for o in offers} == {"a"}
