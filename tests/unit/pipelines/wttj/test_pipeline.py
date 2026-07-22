import types
from typing import Mapping

import pytest

from joblytics.domain.exceptions.errors import NoOffersFoundError
from joblytics.pipelines.base import TimePosted, WorkModality
from joblytics.pipelines.wttj.pipeline import WTTJPipeline


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("joblytics.pipelines.wttj.pipeline.time.sleep", lambda s: None)


class _FakeResponse:
    def __init__(self, text: str = "", ok: bool = True, status_code: int = 200):
        self.text = text
        self.ok = ok
        self.status_code = status_code


def _make_fake_client(*, responses: Mapping[str, _FakeResponse | list[_FakeResponse]]):
    class _FakeClient:
        def __init__(self, config: object, provider: str) -> None:
            self.config = config
            self.provider = provider
            self.scrape_client = types.SimpleNamespace(enable_throttle=False)

        def build_sitemap_index_url(self) -> str:
            return "https://example.com/index"

        def request(self, url: object) -> _FakeResponse:
            key = str(url)
            if key not in responses:
                raise AssertionError(f"unexpected url requested: {key}")
            value = responses[key]
            if isinstance(value, list):
                # A sequence simulates different outcomes across retry
                # attempts for the same URL (e.g. fails once, then
                # succeeds); the last entry repeats once exhausted.
                return value.pop(0) if len(value) > 1 else value[0]
            return value

    return _FakeClient


def _make_fake_parser(
    *,
    shard_urls: list[str],
    urls_by_shard: dict[str, list[str]],
    candidates_by_shard: dict[str, list[str]],
    details_by_url: dict[str, dict[str, object]],
    raise_on_shard_xml: str | None = None,
):
    class _FakeParser:
        def parse_sitemap_index(self, xml: str) -> list[str]:
            return shard_urls

        def parse_job_listing_urls(self, xml: str) -> list[str]:
            if xml == raise_on_shard_xml:
                raise ValueError("mismatched tag: line 21, column 2")
            return urls_by_shard.get(xml, [])

        def filter_candidate_urls(
            self, urls: list[str], title: str, location: str
        ) -> list[str]:
            # keyed by the shard's raw xml text (used as a stand-in id) via
            # the urls list itself, since the fake shard content == its url
            for shard_xml, candidates in candidates_by_shard.items():
                if urls == urls_by_shard.get(shard_xml, []):
                    return candidates
            return []

        def parse_job_detail(self, html: str) -> dict[str, object]:
            return details_by_url.get(html, {})

    return _FakeParser


def _pipeline(
    monkeypatch: pytest.MonkeyPatch,
    *,
    shard_urls: list[str],
    responses: Mapping[str, _FakeResponse | list[_FakeResponse]],
    urls_by_shard: dict[str, list[str]],
    candidates_by_shard: dict[str, list[str]],
    details_by_url: dict[str, dict[str, object]],
    raise_on_shard_xml: str | None = None,
):
    fake_client = _make_fake_client(responses=responses)
    fake_parser = _make_fake_parser(
        shard_urls=shard_urls,
        urls_by_shard=urls_by_shard,
        candidates_by_shard=candidates_by_shard,
        details_by_url=details_by_url,
        raise_on_shard_xml=raise_on_shard_xml,
    )
    monkeypatch.setattr("joblytics.pipelines.wttj.pipeline.WTTJClient", fake_client)
    monkeypatch.setattr("joblytics.pipelines.wttj.pipeline.WTTJParser", fake_parser)
    return WTTJPipeline(
        provider="wttj",
        title="Data Engineer",
        location="Paris",
        time_posted=TimePosted.DAY,
        work_modality=WorkModality.REMOTE,
    )


def _detail(title: str = "Data Engineer", company: str = "Acme") -> dict[str, object]:
    return {"title": title, "company": company, "location": "Paris"}


def test_extract_jobs_returns_enriched_offers(monkeypatch: pytest.MonkeyPatch) -> None:
    pipeline = _pipeline(
        monkeypatch,
        shard_urls=["https://example.com/shard0"],
        responses={
            "https://example.com/index": _FakeResponse(text="index-xml"),
            "https://example.com/shard0": _FakeResponse(text="shard0-xml"),
            "https://example.com/jobs/a": _FakeResponse(text="detail:a"),
            "https://example.com/jobs/b": _FakeResponse(text="detail:b"),
        },
        urls_by_shard={
            "shard0-xml": ["https://example.com/jobs/a", "https://example.com/jobs/b"]
        },
        candidates_by_shard={
            "shard0-xml": ["https://example.com/jobs/a", "https://example.com/jobs/b"]
        },
        details_by_url={
            "detail:a": _detail(company="Acme A"),
            "detail:b": _detail(company="Acme B"),
        },
    )

    offers = pipeline.extract_jobs()

    assert {o.provider_job_id for o in offers} == {"jobs/a", "jobs/b"}
    for offer in offers:
        assert offer.provider == "wttj"
        assert offer.search_title == "Data Engineer"
        assert offer.search_location == "Paris"
        assert offer.search_work_modality == "remote"
        assert offer.search_time_posted == "day"
    companies = {o.provider_job_id: o.company for o in offers}
    assert companies == {"jobs/a": "Acme A", "jobs/b": "Acme B"}


def test_extract_jobs_raises_runtime_error_when_index_exhausts_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline = _pipeline(
        monkeypatch,
        shard_urls=[],
        responses={"https://example.com/index": _FakeResponse(text="bad", ok=False)},
        urls_by_shard={},
        candidates_by_shard={},
        details_by_url={},
    )

    with pytest.raises(RuntimeError, match="sitemap index"):
        pipeline.extract_jobs()


def test_extract_jobs_recovers_shard_that_succeeds_on_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline = _pipeline(
        monkeypatch,
        shard_urls=["https://example.com/shard0"],
        responses={
            "https://example.com/index": _FakeResponse(text="index-xml"),
            # First attempt is WAF-challenged (200 but unparseable to the
            # fake parser, simulated here as ok=False), second succeeds.
            "https://example.com/shard0": [
                _FakeResponse(text="bad", ok=False),
                _FakeResponse(text="shard0-xml"),
            ],
            "https://example.com/jobs/a": _FakeResponse(text="detail:a"),
        },
        urls_by_shard={"shard0-xml": ["https://example.com/jobs/a"]},
        candidates_by_shard={"shard0-xml": ["https://example.com/jobs/a"]},
        details_by_url={"detail:a": _detail()},
    )

    offers = pipeline.extract_jobs()

    assert {o.provider_job_id for o in offers} == {"jobs/a"}


def test_extract_jobs_retries_detail_on_waf_challenge_202_and_recovers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression test: AWS WAF Bot Control returns HTTP 202 for a challenge
    on this site, which `requests.Response.ok` treats as fine (any 2xx) —
    without explicit handling, this was silently read as "no JobPosting
    found" instead of being retried like a real failure."""
    pipeline = _pipeline(
        monkeypatch,
        shard_urls=["https://example.com/shard0"],
        responses={
            "https://example.com/index": _FakeResponse(text="index-xml"),
            "https://example.com/shard0": _FakeResponse(text="shard0-xml"),
            "https://example.com/jobs/a": [
                _FakeResponse(text="challenge-page", ok=True, status_code=202),
                _FakeResponse(text="detail:a"),
            ],
        },
        urls_by_shard={"shard0-xml": ["https://example.com/jobs/a"]},
        candidates_by_shard={"shard0-xml": ["https://example.com/jobs/a"]},
        details_by_url={"detail:a": _detail()},
    )

    offers = pipeline.extract_jobs()

    assert {o.provider_job_id for o in offers} == {"jobs/a"}


def test_extract_jobs_drops_offer_when_all_attempts_hit_waf_challenge_202(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.setenv("WTTJ_DEBUG_CAPTURE_DIR", str(tmp_path))

    pipeline = _pipeline(
        monkeypatch,
        shard_urls=["https://example.com/shard0"],
        responses={
            "https://example.com/index": _FakeResponse(text="index-xml"),
            "https://example.com/shard0": _FakeResponse(text="shard0-xml"),
            "https://example.com/jobs/a": _FakeResponse(
                text="challenge-page", ok=True, status_code=202
            ),
        },
        urls_by_shard={"shard0-xml": ["https://example.com/jobs/a"]},
        candidates_by_shard={"shard0-xml": ["https://example.com/jobs/a"]},
        details_by_url={"detail:a": _detail()},
    )

    offers = pipeline.extract_jobs()

    assert offers == []
    captured = list(tmp_path.glob("detail_exhausted__*.txt"))
    assert len(captured) == 1
    assert captured[0].read_text() == "challenge-page"


def test_extract_jobs_skips_shard_when_parser_raises_on_malformed_xml(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression test: a WAF challenge can swap a shard's body for a short
    non-XML page under HTTP 200, which fails inside the parser itself
    (ElementTree.ParseError), not as an HTTP-level or client-level error."""
    pipeline = _pipeline(
        monkeypatch,
        shard_urls=["https://example.com/shard0", "https://example.com/shard1"],
        responses={
            "https://example.com/index": _FakeResponse(text="index-xml"),
            "https://example.com/shard0": _FakeResponse(text="not-xml"),
            "https://example.com/shard1": _FakeResponse(text="shard1-xml"),
            "https://example.com/jobs/a": _FakeResponse(text="detail:a"),
        },
        urls_by_shard={"shard1-xml": ["https://example.com/jobs/a"]},
        candidates_by_shard={"shard1-xml": ["https://example.com/jobs/a"]},
        details_by_url={"detail:a": _detail()},
        raise_on_shard_xml="not-xml",
    )

    offers = pipeline.extract_jobs()

    assert {o.provider_job_id for o in offers} == {"jobs/a"}


def test_extract_jobs_skips_shard_with_not_ok_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline = _pipeline(
        monkeypatch,
        shard_urls=["https://example.com/shard0", "https://example.com/shard1"],
        responses={
            "https://example.com/index": _FakeResponse(text="index-xml"),
            "https://example.com/shard0": _FakeResponse(text="shard0-xml", ok=False),
            "https://example.com/shard1": _FakeResponse(text="shard1-xml"),
            "https://example.com/jobs/a": _FakeResponse(text="detail:a"),
        },
        urls_by_shard={"shard1-xml": ["https://example.com/jobs/a"]},
        candidates_by_shard={"shard1-xml": ["https://example.com/jobs/a"]},
        details_by_url={"detail:a": _detail()},
    )

    offers = pipeline.extract_jobs()

    assert {o.provider_job_id for o in offers} == {"jobs/a"}


def test_extract_jobs_skips_shard_that_raises_while_fetching_or_parsing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _RaisingResponses(dict[str, _FakeResponse]):
        def __getitem__(self, key: str) -> _FakeResponse:
            if key == "https://example.com/shard0":
                raise RuntimeError("mismatched tag")
            return super().__getitem__(key)

        def __contains__(self, key: object) -> bool:
            return key == "https://example.com/shard0" or super().__contains__(key)

    responses = _RaisingResponses(
        {
            "https://example.com/index": _FakeResponse(text="index-xml"),
            "https://example.com/shard1": _FakeResponse(text="shard1-xml"),
            "https://example.com/jobs/a": _FakeResponse(text="detail:a"),
        }
    )

    pipeline = _pipeline(
        monkeypatch,
        shard_urls=["https://example.com/shard0", "https://example.com/shard1"],
        responses=responses,
        urls_by_shard={"shard1-xml": ["https://example.com/jobs/a"]},
        candidates_by_shard={"shard1-xml": ["https://example.com/jobs/a"]},
        details_by_url={"detail:a": _detail()},
    )

    offers = pipeline.extract_jobs()

    assert {o.provider_job_id for o in offers} == {"jobs/a"}


def test_extract_jobs_stops_scanning_after_shard_cap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # MAX_SHARDS_SCANNED_PER_QUERY is 3; a 4th shard is deliberately left out
    # of `responses` so the fake client raises if it's ever requested.
    pipeline = _pipeline(
        monkeypatch,
        shard_urls=[
            "https://example.com/shard0",
            "https://example.com/shard1",
            "https://example.com/shard2",
            "https://example.com/shard3",
        ],
        responses={
            "https://example.com/index": _FakeResponse(text="index-xml"),
            "https://example.com/shard0": _FakeResponse(text="shard0-xml"),
            "https://example.com/shard1": _FakeResponse(text="shard1-xml"),
            "https://example.com/shard2": _FakeResponse(text="shard2-xml"),
            "https://example.com/jobs/a": _FakeResponse(text="detail:a"),
        },
        urls_by_shard={"shard0-xml": ["https://example.com/jobs/a"]},
        candidates_by_shard={"shard0-xml": ["https://example.com/jobs/a"]},
        details_by_url={"detail:a": _detail()},
    )

    offers = pipeline.extract_jobs()

    assert {o.provider_job_id for o in offers} == {"jobs/a"}


def test_extract_jobs_raises_when_no_candidates_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline = _pipeline(
        monkeypatch,
        shard_urls=["https://example.com/shard0"],
        responses={
            "https://example.com/index": _FakeResponse(text="index-xml"),
            "https://example.com/shard0": _FakeResponse(text="shard0-xml"),
        },
        urls_by_shard={"shard0-xml": ["https://example.com/jobs/a"]},
        candidates_by_shard={"shard0-xml": []},
        details_by_url={},
    )

    with pytest.raises(NoOffersFoundError):
        pipeline.extract_jobs()


def test_extract_jobs_drops_offer_with_not_ok_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline = _pipeline(
        monkeypatch,
        shard_urls=["https://example.com/shard0"],
        responses={
            "https://example.com/index": _FakeResponse(text="index-xml"),
            "https://example.com/shard0": _FakeResponse(text="shard0-xml"),
            "https://example.com/jobs/a": _FakeResponse(text="detail:a", ok=True),
            "https://example.com/jobs/b": _FakeResponse(text="detail:b", ok=False),
        },
        urls_by_shard={
            "shard0-xml": ["https://example.com/jobs/a", "https://example.com/jobs/b"]
        },
        candidates_by_shard={
            "shard0-xml": ["https://example.com/jobs/a", "https://example.com/jobs/b"]
        },
        details_by_url={"detail:a": _detail()},
    )

    offers = pipeline.extract_jobs()

    assert {o.provider_job_id for o in offers} == {"jobs/a"}


def test_extract_jobs_drops_offer_with_no_job_posting_block(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pipeline = _pipeline(
        monkeypatch,
        shard_urls=["https://example.com/shard0"],
        responses={
            "https://example.com/index": _FakeResponse(text="index-xml"),
            "https://example.com/shard0": _FakeResponse(text="shard0-xml"),
            "https://example.com/jobs/a": _FakeResponse(text="detail:a"),
            "https://example.com/jobs/b": _FakeResponse(text="detail:b"),
        },
        urls_by_shard={
            "shard0-xml": ["https://example.com/jobs/a", "https://example.com/jobs/b"]
        },
        candidates_by_shard={
            "shard0-xml": ["https://example.com/jobs/a", "https://example.com/jobs/b"]
        },
        # "detail:b" parses to {} (no JobPosting block found), like a real
        # expired/removed listing would.
        details_by_url={"detail:a": _detail()},
    )

    offers = pipeline.extract_jobs()

    assert {o.provider_job_id for o in offers} == {"jobs/a"}


def test_extract_jobs_captures_skipped_detail_body_when_debug_dir_set(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.setenv("WTTJ_DEBUG_CAPTURE_DIR", str(tmp_path))

    pipeline = _pipeline(
        monkeypatch,
        shard_urls=["https://example.com/shard0"],
        responses={
            "https://example.com/index": _FakeResponse(text="index-xml"),
            "https://example.com/shard0": _FakeResponse(text="shard0-xml"),
            "https://example.com/jobs/a": _FakeResponse(text="stale-listing-body"),
        },
        urls_by_shard={"shard0-xml": ["https://example.com/jobs/a"]},
        candidates_by_shard={"shard0-xml": ["https://example.com/jobs/a"]},
        # "detail:a" maps to {} in the fake parser (no JobPosting found),
        # but the actual captured file must hold the *fetched* body
        # ("stale-listing-body"), not the fake parser's lookup key.
        details_by_url={},
    )

    offers = pipeline.extract_jobs()

    assert offers == []
    captured = list(tmp_path.glob("detail_empty__*.txt"))
    assert len(captured) == 1
    assert captured[0].read_text() == "stale-listing-body"


def test_extract_jobs_does_not_capture_when_debug_dir_unset(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.delenv("WTTJ_DEBUG_CAPTURE_DIR", raising=False)

    pipeline = _pipeline(
        monkeypatch,
        shard_urls=["https://example.com/shard0"],
        responses={
            "https://example.com/index": _FakeResponse(text="index-xml"),
            "https://example.com/shard0": _FakeResponse(text="shard0-xml"),
            "https://example.com/jobs/a": _FakeResponse(text="stale-listing-body"),
        },
        urls_by_shard={"shard0-xml": ["https://example.com/jobs/a"]},
        candidates_by_shard={"shard0-xml": ["https://example.com/jobs/a"]},
        details_by_url={},
    )

    offers = pipeline.extract_jobs()

    assert offers == []
    assert list(tmp_path.iterdir()) == []


def test_extract_jobs_drops_offer_when_detail_request_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _RaisingResponses(dict[str, _FakeResponse]):
        def __getitem__(self, key: str) -> _FakeResponse:
            if key == "https://example.com/jobs/b":
                raise RuntimeError("network error")
            return super().__getitem__(key)

        def __contains__(self, key: object) -> bool:
            return key == "https://example.com/jobs/b" or super().__contains__(key)

    responses = _RaisingResponses(
        {
            "https://example.com/index": _FakeResponse(text="index-xml"),
            "https://example.com/shard0": _FakeResponse(text="shard0-xml"),
            "https://example.com/jobs/a": _FakeResponse(text="detail:a"),
        }
    )

    pipeline = _pipeline(
        monkeypatch,
        shard_urls=["https://example.com/shard0"],
        responses=responses,
        urls_by_shard={
            "shard0-xml": ["https://example.com/jobs/a", "https://example.com/jobs/b"]
        },
        candidates_by_shard={
            "shard0-xml": ["https://example.com/jobs/a", "https://example.com/jobs/b"]
        },
        details_by_url={"detail:a": _detail()},
    )

    offers = pipeline.extract_jobs()

    assert {o.provider_job_id for o in offers} == {"jobs/a"}
