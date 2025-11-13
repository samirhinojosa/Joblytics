from pydantic import HttpUrl
import types
from typing import Optional
import requests
import pytest
from pathlib import Path
from app.infrastructure.http.header_provider import RandomHeaderProvider
from app.infrastructure.http.scraper.scrape_client import ScrapeClient


@pytest.fixture
def valid_ua_file(tmp_path: Path) -> Path:
    # A desktop UA line (>= 60 chars, not mobile)
    line = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    p = tmp_path / "user_agents.txt"
    p.write_text("# comment\n" + line + "\n", encoding="utf-8", newline="")
    return p


class DummyHeaderProvider(RandomHeaderProvider):
    def header(self, url: HttpUrl) -> dict[str, str]:
        return {"User-Agent": "pytest-UA"}


def test_web_page(monkeypatch, valid_ua_file: Path) -> None:
    client = ScrapeClient(
        web_url=HttpUrl("http://example.com/jobs"),
        header_provider=DummyHeaderProvider(ua_file=valid_ua_file),
    )

    class FakeResponse:
        def __init__(
            self,
            status_code: int = 200,
            headers: Optional[dict] = None,
            text: str = "OK",
        ):
            self.status_code = 200
            self.headers: dict = headers or {}
            self._text = text

        @property
        def ok(self) -> bool:
            return 200 <= self.status_code < 400

        @property
        def text(self) -> str:
            return self._text

        def raise_for_status(self) -> None:
            if not self.ok:
                raise requests.HTTPError(f"HTTP {self.status_code}")

    def fake_get(self, url, headers=None, timeout=None):
        assert headers and headers.get("User-Agent") == "pytest-UA"
        return FakeResponse(200)

    # Bind the function as a bound method on this instance
    bound = types.MethodType(fake_get, client._session)
    monkeypatch.setattr(client._session, "get", bound)

    response = client.web_page_search()
    assert response.status_code == 200


def test_get_backoff_sleep_basic(monkeypatch, valid_ua_file: Path) -> None:
    # Freeze jitter to a fixed value on the module where it's used
    monkeypatch.setattr(
        "app.infrastructure.http.scraper.scrape_client.random.uniform",
        lambda a, b: 0.25,
        raising=True,
    )

    scrape_client = ScrapeClient(
        web_url=HttpUrl("https://example.com"),
        header_provider=DummyHeaderProvider(ua_file=valid_ua_file),
        backoff_factor=1.0,  # so base = 1 * 2^(attempt-1)
        backoff_cap=30.0,  # high enough not to cap in these attempts
    )

    # Freeze jitter to a fixed value
    monkeypatch.setattr("random.uniform", lambda a, b: 0.25)

    # attempt = 1 → base=1*(2^(1-1)) = 1
    assert scrape_client._get_backoff_sleep(1) == 1 + 0.25

    # attempt = 3 → base = 1*(2^(3-1)) = 4
    assert scrape_client._get_backoff_sleep(3) == 4 + 0.25


def test_web_page_retryable_with_numeric_retry_after(
    monkeypatch, valid_ua_file: Path
) -> None:
    # Local FakeResponse matching your style
    class FakeResponse:
        def __init__(
            self,
            status_code: int = 200,
            headers: Optional[dict] = None,
            text: str = "OK",
        ):
            self.status_code = status_code
            self.headers: dict = headers or {}
            self._text = text

        @property
        def ok(self) -> bool:
            return 200 <= self.status_code < 400

        @property
        def text(self) -> str:
            return self._text

        def raise_for_status(self) -> None:
            if not self.ok:
                raise requests.HTTPError(f"HTTP {self.status_code}")

    client = ScrapeClient(
        web_url=HttpUrl("http://example.com/jobs"),
        header_provider=DummyHeaderProvider(ua_file=valid_ua_file),
    )

    sleeps = []
    monkeypatch.setattr("time.sleep", lambda s: sleeps.append(s))

    # First call: 429 with numeric Retry-After -> sleep exact value; Second call: 200 OK
    seq = [
        FakeResponse(status_code=429, headers={"Retry-After": "1.75"}),
        FakeResponse(status_code=200),
    ]

    def fake_get(self, url, headers=None, timeout=None):
        assert headers and headers.get("User-Agent") == "pytest-UA"
        return seq.pop(0)

    bound = types.MethodType(fake_get, client._session)
    monkeypatch.setattr(client._session, "get", bound)

    resp = client.web_page_search()
    assert resp.ok is True
    assert sleeps == [1.75]


def test_web_page_retryable_with_malformed_retry_after_uses_backoff(
    monkeypatch, valid_ua_file: Path
) -> None:
    class FakeResponse:
        def __init__(self, status_code: int = 200, headers: Optional[dict] = None):
            self.status_code = status_code
            self.headers: dict = headers or {}

        @property
        def ok(self) -> bool:
            return 200 <= self.status_code < 400

        def raise_for_status(self) -> None:
            if not self.ok:
                raise requests.HTTPError(f"HTTP {self.status_code}")

    client = ScrapeClient(
        web_url=HttpUrl("http://example.com/jobs"),
        header_provider=DummyHeaderProvider(ua_file=valid_ua_file),
    )

    sleeps = []
    monkeypatch.setattr("time.sleep", lambda s: sleeps.append(s))

    # Make backoff deterministic for attempt=1
    monkeypatch.setattr(
        "app.infrastructure.http.scraper.scrape_client.ScrapeClient._get_backoff_sleep",
        lambda self, attempt: 0.3,
        raising=True,
    )

    seq = [
        FakeResponse(
            status_code=503, headers={"Retry-After": "abc"}
        ),  # malformed -> fallback to backoff
        FakeResponse(status_code=200),
    ]

    def fake_get(self, url, headers=None, timeout=None):
        assert headers and headers.get("User-Agent") == "pytest-UA"
        return seq.pop(0)

    bound = types.MethodType(fake_get, client._session)
    monkeypatch.setattr(client._session, "get", bound)

    resp = client.web_page_search()
    assert resp.ok is True
    assert sleeps == [0.3]


def test_web_page_non_retryable_raises_then_retries_via_exception(
    monkeypatch, valid_ua_file: Path
) -> None:
    class FakeResponse:
        def __init__(self, status_code: int = 200):
            self.status_code = status_code
            self.headers: dict = {}

        @property
        def ok(self) -> bool:
            return 200 <= self.status_code < 400

        def raise_for_status(self) -> None:
            if not self.ok:
                raise requests.HTTPError(f"HTTP {self.status_code}")

    client = ScrapeClient(
        web_url=HttpUrl("http://example.com/jobs"),
        header_provider=DummyHeaderProvider(ua_file=valid_ua_file),
    )

    sleeps = []
    monkeypatch.setattr("time.sleep", lambda s: sleeps.append(s))
    # Deterministic backoff
    monkeypatch.setattr(
        "app.infrastructure.http.scraper.scrape_client.ScrapeClient._get_backoff_sleep",
        lambda self, attempt: 0.2,
        raising=True,
    )

    # First: 404 (non-retryable) -> raise_for_status -> caught as RequestException -> sleep -> retry -> 200
    seq = [
        FakeResponse(status_code=404),
        FakeResponse(status_code=200),
    ]

    def fake_get(self, url, headers=None, timeout=None):
        assert headers and headers.get("User-Agent") == "pytest-UA"
        return seq.pop(0)

    bound = types.MethodType(fake_get, client._session)
    monkeypatch.setattr(client._session, "get", bound)

    resp = client.web_page_search()
    assert resp.ok is True
    assert sleeps == [0.2]


def test_web_page_last_attempt_retryable_raises_scrape_client_error(
    monkeypatch, valid_ua_file: Path
) -> None:
    from app.infrastructure.http.scraper.scrape_client_error import ScrapeClientError

    class FakeResponse:
        def __init__(self, status_code: int = 200, raise_http: bool = False):
            self.status_code = status_code
            self.headers: dict = {}
            self._raise_http = raise_http

        @property
        def ok(self) -> bool:
            return 200 <= self.status_code < 400

        def raise_for_status(self) -> None:
            if self._raise_http or not self.ok:
                raise requests.HTTPError(f"HTTP {self.status_code}")

    client = ScrapeClient(
        web_url=HttpUrl("http://example.com/jobs"),
        header_provider=DummyHeaderProvider(ua_file=valid_ua_file),
        max_retries=2,  # make it short and explicit
    )

    # No real sleeping
    monkeypatch.setattr("time.sleep", lambda s: None)
    # Deterministic backoff for attempt 1
    monkeypatch.setattr(
        "app.infrastructure.http.scraper.scrape_client.ScrapeClient._get_backoff_sleep",
        lambda self, attempt: 0.1,
        raising=True,
    )

    # Attempt 1: 500 (retryable) -> sleep & retry
    # Attempt 2 (last): 500 (retryable) -> raise_for_status -> caught -> ScrapeClientError
    seq = [
        FakeResponse(status_code=500, raise_http=False),
        FakeResponse(status_code=500, raise_http=True),
    ]

    def fake_get(self, url, headers=None, timeout=None):
        assert headers and headers.get("User-Agent") == "pytest-UA"
        return seq.pop(0)

    bound = types.MethodType(fake_get, client._session)
    monkeypatch.setattr(client._session, "get", bound)

    with pytest.raises(ScrapeClientError):
        client.web_page_search()


@pytest.fixture
def empty_or_invalid_file(tmp_path: Path) -> Path:
    p = tmp_path / "empty.txt"
    p.write_text("# only comments\n# and short\nShort\n", encoding="utf-8", newline="")
    return p


@pytest.fixture
def ua_file_invalid(tmp_path: Path) -> Path:
    """
    UA file that should produce an empty 'uas' list after filtering -> triggers ValueError at ~ line 57.
    """
    p = tmp_path / "invalid_uas.txt"
    lines = [
        "# only comments\n",
        "Short\n",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_2 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1\n",
        "Mozilla/5.0 (Linux; Android 13; SM-XXXX) AppleWebKit/537.36 Mobile Safari/537.36\n",
    ]
    p.write_text("".join(lines), encoding="utf-8", newline="")
    return p


def test_missing_file_header_provider(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist.txt"
    with pytest.raises(FileNotFoundError):
        RandomHeaderProvider(ua_file=missing)


def test_empty_or_invalid_file_raises_header_provider(
    empty_or_invalid_file: Path,
) -> None:
    with pytest.raises(ValueError):
        RandomHeaderProvider(ua_file=empty_or_invalid_file)


def test_invalid_after_filtering_triggers_valueerror_header_provider(
    ua_file_invalid: Path,
) -> None:
    with pytest.raises(ValueError):
        RandomHeaderProvider(ua_file=ua_file_invalid)


@pytest.mark.parametrize(
    "url, expected_referer",
    [
        # Covers the '/seeMoreJobPostings/' sub-branch in header() -> lines 66-70ish
        (
            "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/somepath",
            "https://www.linkedin.com/jobs/view/",
        ),
        # Covers the '/jobPosting/' sub-branch in header() -> lines 70-73ish
        (
            "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/123456",
            "https://www.linkedin.com/jobs/search",
        ),
        # Covers the 'linkedin' outer if, but no inner match => no Referer set -> lines 63-85 overall block
        (
            "https://www.linkedin.com/feed/",
            None,
        ),
        # Covers the else path when 'linkedin' not in URL -> skips block entirely
        (
            "https://example.com/",
            None,
        ),
    ],
)
def test_header_linkedin_referer_logic_header_provider(
    url: str, expected_referer: str | None, valid_ua_file: Path
) -> None:
    rhp = RandomHeaderProvider(ua_file=valid_ua_file)
    h = rhp.header(HttpUrl(url))  # let Pydantic validate/coerce

    # Standard keys always present
    for k in [
        "User-Agent",
        "Accept",
        "Accept-Language",
        "Accept-Encoding",
        "Connection",
        "Upgrade-Insecure-Requests",
        "DNT",
    ]:
        assert k in h

    if expected_referer is None:
        assert "Referer" not in h
    else:
        assert h.get("Referer") == expected_referer
