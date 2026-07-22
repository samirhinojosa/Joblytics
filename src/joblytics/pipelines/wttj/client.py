from pydantic import HttpUrl
import logging
import requests
from .models import WTTJConfig
from .constants import WTTJ_SITEMAP_INDEX_URL
from joblytics.infrastructure.http.scraping.http_client import ScrapeClient


class WTTJClient:
    def __init__(self, config: WTTJConfig, provider: str):
        self.config = config
        self.provider = provider
        self.logger = logging.getLogger("joblytics")

        # Base client
        self.scrape_client = ScrapeClient(
            provider=self.provider,
            web_url=HttpUrl(WTTJ_SITEMAP_INDEX_URL),
            enable_throttle=False,
        )

    def build_sitemap_index_url(self) -> HttpUrl:
        """
        Builds the URL of WTTJ's public sitemap index.

        Returns:
            HttpUrl: The sitemap index URL.
        """
        return HttpUrl(WTTJ_SITEMAP_INDEX_URL)

    def request(self, url: HttpUrl) -> requests.Response:
        """
        Executes a network request to a specific WTTJ URL (sitemap shard or
        job detail page).

        This method acts as the centralized gateway for all HTTP communication
        within the WTTJ pipeline.

        Args:
            url (HttpUrl): The target WTTJ URL to fetch.

        Returns:
            requests.Response: The complete HTTP response object. `requests`
                transparently decompresses the sitemap's gzip
                Content-Encoding, so `.text` already holds plain XML/HTML.
        """
        try:
            return self.scrape_client.web_page_search(web_url=url)
        except Exception as e:
            self.logger.error(f"Error in the request to {url}: {e}")
            raise
