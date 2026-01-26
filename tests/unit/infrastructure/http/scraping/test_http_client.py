from pydantic import HttpUrl
import types
from typing import Optional
import requests
import pytest
from pathlib import Path

from joblytics.infrastructure.http.scraping.headers import RandomHeaderProvider
from joblytics.infrastructure.http.scraping.http_client import ScrapeClient
from joblytics.infrastructure.http.scraping.policies.policy import HttpPolicy


@pytest.fixture
def valid_ua_file(tmp_path: Path) -> Path:
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


def _patch_settings(monkeypatch, *, provider: str, policy: HttpPolicy) -> None:
    """
    Monkeypatch get_settings() in the http_client module so ScrapeClient
    always resolves a deterministic policy for tests.
    """

    class FakeSettings:
        def http_policy(self, p: str) -> HttpPolicy:
            assert p == provider
            return policy

    monkeypatch.setattr(
        "joblytics.infrastructure.http.scraping.http_client.get_settings",
        lambda: FakeSettings(),
        raising=True,
    )


def test_web_page(monkeypatch, valid_ua_file: Path) -> None:
    _patch_settings(
        monkeypatch,
        provider="linkedin",
        policy=HttpPolicy(max_retries=1),  # keep minimal
    )

    client = ScrapeClient(
        provider="linkedin",
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

    def fake_get(self, url, headers=None, timeout=None):
        assert headers and headers.get("User-Agent") == "pytest-UA"
        return FakeResponse(200)

    bound = types.MethodType(fake_get, client._session)
    monkeypatch.setattr(client._session, "get", bound)

    response = client.web_page_search()
    assert response.status_code == 200


def test_get_backoff_sleep_basic(monkeypatch, valid_ua_file: Path) -> None:
    # policy determinista: backoff_factor=1.0; cap alto
    _patch_settings(
        monkeypatch,
        provider="linkedin",
        policy=HttpPolicy(backoff_factor=1.0, backoff_cap=30.0, max_retries=3),
    )

    # Freeze jitter inside the module where it's used
    monkeypatch.setattr(
        "joblytics.infrastructure.http.scraping.http_client.random.uniform",
        lambda a, b: 0.25,
        raising=True,
    )

    client = ScrapeClient(
        provider="linkedin",
        web_url=HttpUrl("https://example.com"),
        header_provider=DummyHeaderProvider(ua_file=valid_ua_file),
    )

    # attempt=1 -> base = 1.0 * 2^(0) = 1.0
    assert client._get_backoff_sleep(1) == 1.0 + 0.25

    # attempt=3 -> base = 1.0 * 2^(2) = 4.0
    assert client._get_backoff_sleep(3) == 4.0 + 0.25


def test_web_page_retryable_with_numeric_retry_after(
    monkeypatch, valid_ua_file: Path
) -> None:
    _patch_settings(
        monkeypatch,
        provider="linkedin",
        policy=HttpPolicy(max_retries=2),  # 1 retry
    )

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
        provider="linkedin",
        web_url=HttpUrl("http://example.com/jobs"),
        header_provider=DummyHeaderProvider(ua_file=valid_ua_file),
    )

    sleeps: list[float] = []
    monkeypatch.setattr("time.sleep", lambda s: sleeps.append(float(s)))

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
    _patch_settings(
        monkeypatch,
        provider="linkedin",
        policy=HttpPolicy(max_retries=2),
    )

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
        provider="linkedin",
        web_url=HttpUrl("http://example.com/jobs"),
        header_provider=DummyHeaderProvider(ua_file=valid_ua_file),
    )

    sleeps: list[float] = []
    monkeypatch.setattr("time.sleep", lambda s: sleeps.append(float(s)))

    # deterministic backoff
    monkeypatch.setattr(
        "joblytics.infrastructure.http.scraping.http_client.ScrapeClient._get_backoff_sleep",
        lambda self, attempt: 0.3,
        raising=True,
    )

    seq = [
        FakeResponse(status_code=503, headers={"Retry-After": "abc"}),
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
    _patch_settings(
        monkeypatch,
        provider="linkedin",
        policy=HttpPolicy(max_retries=2),
    )

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
        provider="linkedin",
        web_url=HttpUrl("http://example.com/jobs"),
        header_provider=DummyHeaderProvider(ua_file=valid_ua_file),
    )

    sleeps: list[float] = []
    monkeypatch.setattr("time.sleep", lambda s: sleeps.append(float(s)))

    monkeypatch.setattr(
        "joblytics.infrastructure.http.scraping.http_client.ScrapeClient._get_backoff_sleep",
        lambda self, attempt: 0.2,
        raising=True,
    )

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
    from joblytics.infrastructure.http.scraping.errors import (
        ScrapeClientError,
    )

    _patch_settings(
        monkeypatch,
        provider="linkedin",
        policy=HttpPolicy(max_retries=2),
    )

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
        provider="linkedin",
        web_url=HttpUrl("http://example.com/jobs"),
        header_provider=DummyHeaderProvider(ua_file=valid_ua_file),
    )

    monkeypatch.setattr("time.sleep", lambda s: None)

    monkeypatch.setattr(
        "joblytics.infrastructure.http.scraping.http_client.ScrapeClient._get_backoff_sleep",
        lambda self, attempt: 0.1,
        raising=True,
    )

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
        (
            "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/somepath",
            "https://www.linkedin.com/jobs/view/",
        ),
        (
            "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/123456",
            "https://www.linkedin.com/jobs/search",
        ),
        ("https://www.linkedin.com/feed/", None),
        ("https://example.com/", None),
    ],
)
def test_header_linkedin_referer_logic_header_provider(
    url: str, expected_referer: str | None, valid_ua_file: Path
) -> None:
    rhp = RandomHeaderProvider(ua_file=valid_ua_file)
    h = rhp.header(HttpUrl(url))

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
