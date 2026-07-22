import pytest

from joblytics.infrastructure.http.scraping.http_client import ScrapeClient
from joblytics.pipelines.wttj.client import WTTJClient
from joblytics.pipelines.wttj.constants import WTTJ_SITEMAP_INDEX_URL
from joblytics.pipelines.wttj.models import WTTJConfig


@pytest.fixture
def client() -> WTTJClient:
    config = WTTJConfig(title="Data Engineer", location="Paris")
    return WTTJClient(config, provider="wttj")


def test_build_sitemap_index_url_returns_the_fixed_index_url(
    client: WTTJClient,
) -> None:
    assert str(client.build_sitemap_index_url()) == WTTJ_SITEMAP_INDEX_URL


def test_request_delegates_to_scrape_client(
    client: WTTJClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    sentinel = object()
    captured: dict[str, object] = {}

    def fake_web_page_search(self, web_url=None):
        captured["web_url"] = web_url
        return sentinel

    monkeypatch.setattr(ScrapeClient, "web_page_search", fake_web_page_search)

    url = client.build_sitemap_index_url()
    result = client.request(url)

    assert result is sentinel
    assert captured["web_url"] == url


def test_request_logs_and_reraises_on_error(
    client: WTTJClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_web_page_search(self, web_url=None):
        raise RuntimeError("network down")

    monkeypatch.setattr(ScrapeClient, "web_page_search", fake_web_page_search)

    with pytest.raises(RuntimeError, match="network down"):
        client.request(client.build_sitemap_index_url())
