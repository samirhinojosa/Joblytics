from urllib.parse import urlencode, quote_plus
from pydantic import HttpUrl
from typing import Any
import time
import random
import logging
import requests
from .models import LinkedInConfig
from .constants import (
    LINKEDIN_SEARCH_URL,
    LINKEDIN_API_SEARCH_URL,
    LINKEDIN_DETAILS_URL,
)
from joblytics.infrastructure.http.scraping.http_client import ScrapeClient


class LinkedInClient:
    def __init__(self, config: LinkedInConfig, provider: str):
        self.config = config
        self.provider = provider
        self.logger = logging.getLogger("joblytics")

        # Base client
        self.scrape_client = ScrapeClient(
            provider=self.provider,
            web_url=HttpUrl(LINKEDIN_SEARCH_URL),
            enable_throttle=False,
        )

    def build_search_url(
        self, offset: int | None = None, geo_id: int | None = None
    ) -> HttpUrl:
        """
        Builds the LinkedIn job search URL for both initial search and pagination

        It uses the validated search parameters from the model configuration and
        switches the base URL depending on whether pagination is required.

        Args:
            offset (int, optional): Pagination offset for job listings. Defaults to None.
            geo_id (int, optional): LinkedIn-specific geographic identifier to restrict the search area. Defaults to None.

        Returns:
            HttpUrl: The fully encoded LinkedIn job search or pagination URL.
        """

        base = LINKEDIN_API_SEARCH_URL if offset is not None else LINKEDIN_SEARCH_URL

        params: dict[str, Any] = {
            "keywords": self.config.title,
            "location": self.config.location,
            "distance": self.config.distance,
        }

        if self.config.time_posted_value:
            params["f_TPR"] = self.config.time_posted_value
        if self.config.work_modality_value:
            params["f_WT"] = self.config.work_modality_value

        if offset is not None:
            pagination_params: dict[str, Any] = {
                "start": offset,
                "count": self.config.PAGE_SIZE,
                "position": 1,
                "pageNum": 0,
            }
            params.update(pagination_params)
            if geo_id:
                params["geoId"] = geo_id

        query_string = urlencode(params, quote_via=quote_plus)

        return HttpUrl(f"{base}?{query_string}")

    def build_detail_url(self, job_id: str) -> HttpUrl:
        """
        Constructs the URL to fetch the full details of a specific job offer.

        Args:
            job_id (str): The unique LinkedIn job identifier.

        Returns:
            str: The full URL for the guest-facing job posting API.
        """
        return HttpUrl(f"{LINKEDIN_DETAILS_URL}{job_id}")

    def request(self, url: HttpUrl) -> requests.Response:
        """
        Executes a network request to a specific LinkedIn URL.

        This method acts as the centralized gateway for all HTTP communication
        within the LinkedIn pipeline.

        Args:
            url (str): The target LinkedIn URL to fetch, which can be a
                search result page, an API pagination endpoint, or a
                job detail page.

        Returns:
            requests.Response: The complete HTTP response object, allowing
                access to status codes, headers, and the raw HTML body.
        """
        try:
            return self.scrape_client.web_page_search(web_url=url)
        except Exception as e:
            self.logger.error(f"Error in the request to {url}: {e}")
            raise
