from pydantic import HttpUrl
import types
from typing import Optional
import requests
from app.infrastructure.http.header_provider import RandomHeaderProvider
from app.infrastructure.http.scraper.scrape_client import ScrapeClient


class DummyHeaderProvider(RandomHeaderProvider):
    def header(self, url: HttpUrl) -> dict[str, str]:
        return {"User-Agent": "pytest-UA"}


def test_web_page(monkeypatch) -> None:
    client = ScrapeClient(
        web_url=HttpUrl("http://example.com/jobs"),
        header_provider=DummyHeaderProvider(),
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
