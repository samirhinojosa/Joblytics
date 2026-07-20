from urllib.parse import parse_qs, urlparse

import pytest

from joblytics.infrastructure.http.scraping.http_client import ScrapeClient
from joblytics.pipelines.base import TimePosted, WorkModality
from joblytics.pipelines.linkedin.client import LinkedInClient
from joblytics.pipelines.linkedin.constants import (
    LINKEDIN_API_SEARCH_URL,
    LINKEDIN_DETAILS_URL,
    LINKEDIN_SEARCH_URL,
)
from joblytics.pipelines.linkedin.models import LinkedInConfig


def _query(url: str) -> dict[str, list[str]]:
    return parse_qs(urlparse(url).query)


@pytest.fixture
def client() -> LinkedInClient:
    config = LinkedInConfig(title="Data Engineer", location="Paris")
    return LinkedInClient(config, provider="linkedin")


def test_build_search_url_initial_uses_base_search_url(client: LinkedInClient) -> None:
    url = str(client.build_search_url())
    assert url.startswith(LINKEDIN_SEARCH_URL)

    params = _query(url)
    assert params["keywords"] == ["Data Engineer"]
    assert params["location"] == ["Paris"]
    assert params["distance"] == ["10"]
    assert "f_TPR" not in params
    assert "f_WT" not in params


def test_build_search_url_includes_filters_when_set() -> None:
    config = LinkedInConfig(
        title="Data Engineer",
        location="Paris",
        time_posted=TimePosted.DAY,
        work_modality=WorkModality.REMOTE,
    )
    client = LinkedInClient(config, provider="linkedin")

    params = _query(str(client.build_search_url()))
    assert params["f_TPR"] == ["r86400"]
    assert params["f_WT"] == ["3"]


def test_build_search_url_pagination_uses_api_url_and_params(
    client: LinkedInClient,
) -> None:
    url = str(client.build_search_url(offset=20, geo_id=102277331))
    assert url.startswith(LINKEDIN_API_SEARCH_URL)

    params = _query(url)
    assert params["start"] == ["20"]
    assert params["count"] == ["10"]
    assert params["geoId"] == ["102277331"]


def test_build_search_url_pagination_without_geo_id_omits_it(
    client: LinkedInClient,
) -> None:
    url = str(client.build_search_url(offset=0))
    assert "geoId" not in _query(url)


def test_build_detail_url_appends_job_id(client: LinkedInClient) -> None:
    url = str(client.build_detail_url("123456"))
    assert url == f"{LINKEDIN_DETAILS_URL}123456"


def test_request_delegates_to_scrape_client(
    client: LinkedInClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    sentinel = object()
    captured: dict[str, object] = {}

    def fake_web_page_search(self, web_url=None):
        captured["web_url"] = web_url
        return sentinel

    monkeypatch.setattr(ScrapeClient, "web_page_search", fake_web_page_search)

    url = client.build_detail_url("1")
    result = client.request(url)

    assert result is sentinel
    assert captured["web_url"] == url


def test_request_logs_and_reraises_on_error(
    client: LinkedInClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_web_page_search(self, web_url=None):
        raise RuntimeError("network down")

    monkeypatch.setattr(ScrapeClient, "web_page_search", fake_web_page_search)

    with pytest.raises(RuntimeError, match="network down"):
        client.request(client.build_detail_url("1"))
