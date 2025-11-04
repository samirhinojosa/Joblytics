import re
import requests
import math
from enum import Enum
import logging
import time
import random
from pydantic import BaseModel, ConfigDict, Field, field_validator, PrivateAttr, HttpUrl
from typing import Annotated, Optional
from urllib.parse import urlencode, quote_plus
from bs4 import BeautifulSoup, Tag
from itertools import zip_longest, chain
from concurrent.futures import ThreadPoolExecutor
import threading
from app.infrastructure.http.scraper.scrape_client import ScrapeClient
from app.domain.exceptions import NoOffersFoundError
from app.infrastructure.http.scraper.scrape_client_error import ScrapeClientError


logger = logging.getLogger(__name__)

print("hello"

class TimePosted(str, Enum):
    ALL = ""
    DAY = "r86400"
    WEEK = "r604800"
    MONTH = "r2592000"

class RemoteMode(str, Enum):
    ALL = ""
    ONSITE = "1"
    HYBRID = "2"
    REMOTE = "3"

class LinkedInScrapper(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    title: Annotated[str, Field(min_length=1, description="Job title")]
    location: Annotated[str, Field(min_length=1, description="Job location")]
    distance: Annotated[int, Field(ge=0, le=100, description="Search radius")] = 10
    time_posted: TimePosted = TimePosted.ALL
    remote_mode: RemoteMode = RemoteMode.ALL

    # Config global
    PAGE_SIZE: int = 10

    # Normalizes input strings
    @field_validator("title", "location")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    def generate_jobs_url(
            self,
            title: Optional[str] = None,
            location: Optional[str] = None,
            distance: Optional[int] = None,
            geo_id: Optional[int] = None,
            offset: Optional[int] = None,
            time_posted: Optional[TimePosted] = None,
            remote_mode: Optional[RemoteMode] = None
    ) -> HttpUrl:
        """
        Generate the LinkedIn job search URL using the model values (and allowing for occasional overrides)
        """
        params = {
            "keywords" : (title or self.title),
            "location" : (location or self.location),
            "distance": (distance if distance is not None else self.distance)
        }

        tp = (time_posted or self.time_posted).value
        if tp:
            params["f_TPR"] = tp

        rm = (remote_mode or self.remote_mode).value
        if rm:
            params["f_WT"] = rm

        if offset is not None:
            BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            if geo_id is not None:
                params["geoId"] = geo_id
            params["position"] = 1
            params["pageNum"] = 0
            params["start"] = offset
            params["count"] = self.PAGE_SIZE
        else:
            BASE_URL = "https://www.linkedin.com/jobs/search"

        return HttpUrl(f"{BASE_URL}?{urlencode(params, quote_via=quote_plus)}")


    def number_of_offers(
            self,
            response: requests.Response
    ) -> int:
        """
        Getting the number of offers
        """
        soup = BeautifulSoup(response.text, "html.parser")
        node = soup.select_one("span.results-context-header__job-count")
        count = int(re.sub(r"\D+", "", node.get_text(strip=True))) if node else 0

        return count


    def _extract_geo_id(self, response: requests.Response) -> int | None:
        """
        Extract the geoId value from the main search page HTML.
        Returns None if not found.
        """
        try:
            soup = BeautifulSoup(response.text, "html.parser")
            node = soup.select_one('form#jserp-filters input[name="geoId"]')

            if not node:
                logger.debug("geoId not found in HTML")
                return None

            geo_id = node.get("value", "").strip()
            if geo_id.isdigit():
                return int(geo_id)
            else:
                logger.debug(f"geoId found but invalid: {geo_id}")
                return None
        except Exception as e:
            logger.warning(f"Failed to extract geoId: {e}")
            return None


    def _polite_delay(self, base: float = 0.6, jitter: float = 0.5):
        """
        Short pause with jitter to avoid sending a lot of requests to the detail endpoint.
        """
        time.sleep(base + random.random() * jitter)


    def fetch_offers_summary(
            self,
    ) -> list[dict]:
        """
        Goes through the pagination of the LinkedIn jobs listings and return an offers basic list
        """
        try:
            logger.info(f"[Summary] Starting LinkedIn jobs listings fetch: [title='{self.title}', location='{self.location}', "
                        f"time_posted='{self.time_posted.name.lower()}']...")

            url = self.generate_jobs_url()
            scrape_client = ScrapeClient(web_url=url)
            response = scrape_client.web_page_search()
            number_of_offers = self.number_of_offers(response)
            geo_id = self._extract_geo_id(response)

            MAX_START = min(975, number_of_offers - 1)  # Avoiding to request empty webpages

            if number_of_offers <= 0:
                logger.warning(
                    f"Zero results reported by counter — possible empty page or authwall. "
                    f"status={response.status_code}, url={response.url}, len(html)={len(response.text)}"
                )
                raise NoOffersFoundError(
                    title=self.title,
                    location=self.location,
                    distance=self.distance,
                    time_posted=self.time_posted.name.lower(),
                    remote_mode=self.remote_mode.name.lower(),
                    url=self.generate_jobs_url()
                )

            if number_of_offers > 1000:
                logger.warning(f"[Summary] Processing capped at 1,000 offers to avoid LinkedIn rate limits (total {number_of_offers})")

            jobs_summary = []
            for i in range(0, MAX_START + 1, self.PAGE_SIZE):

                if random.random() < 0.6: # print with 60% probability
                    logger.info(f"[Summary] Fetching batch {i}-{i + self.PAGE_SIZE} of {number_of_offers} job listings...")

                _url = self.generate_jobs_url(offset=i, geo_id=geo_id)
                self._polite_delay(base=0.45, jitter=0.4)
                response = scrape_client.web_page_search(web_url=_url)
                soup = BeautifulSoup(response.text, "html.parser")
                soup_jobs = soup.find_all("li")

                for job in soup_jobs:
                    if not isinstance(job, Tag):
                        continue

                    cards = job.select("div.base-card[data-entity-urn]")
                    for card in cards:
                        job_id_card = card.get("data-entity-urn")
                        job_id = job_id_card.split(":")[-1] if job_id_card else None
                        if not job_id:
                            continue

                        title_card = job.select_one("h3.base-search-card__title")
                        title = title_card.get_text(strip=True) if title_card else None

                        company_card = job.select_one("h4.base-search-card__subtitle")
                        company = company_card.get_text(strip=True) if company_card else None

                        location_card = job.select_one("span.job-search-card__location")
                        location = location_card.get_text(strip=True) if location_card else None

                        url_card = job.select_one("a.base-card__full-link")
                        url = url_card.get("href") if url_card else None

                        job_details = {
                            "id" : job_id,
                            "title" : title,
                            "company" : company,
                            "location" : location,
                            "url": url
                        }

                        jobs_summary.append(job_details)

            logger.info(f"[Summary] Completed LinkedIn job summary fetch: {len(jobs_summary)}/{number_of_offers} "
                        f"listings retrieved [title='{self.title}', location='{self.location}', "
                        f"time_posted='{self.time_posted.name.lower()}'].")
            return jobs_summary

        except NoOffersFoundError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error while fetching LinkedIn offers summary: {type(e).__name__} - {e}")
            return []


    def fetch_offers_details(
            self,
            jobs: list[dict]
    ) -> list[dict] | None:

        if not jobs:
            return None

        COUNT_TOTAL = len(jobs)
        logger.info(f"[Details] Starting LinkedIn jobs details fetch: {COUNT_TOTAL} listings to process.")

        MAX_WORKERS = 5
        BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/"

        # Split the list into chunks of 5 dictionaries each using zip_longest
        # (fills missing values with None and filters them out)
        jobs_lists = [list(filter(None, job)) for job in zip_longest(*[iter(jobs)]*MAX_WORKERS)]

        # shared counter
        done = 0
        lock = threading.Lock()
        def _fetch_offers_details(_jobs: list) -> None:

            scrape_client = ScrapeClient(web_url=HttpUrl(f"{BASE_URL}{int(_jobs[0]["id"])}"))
            nonlocal done

            for job in _jobs:
                try:

                    with lock:
                        done += 1

                    if random.random() < 0.4: # print with 40% probability
                        logger.info(f"[Details] Fetching jobs details {done}/{COUNT_TOTAL} (id={job['id']})")

                    job_id_url = HttpUrl(f"{BASE_URL}{int(job['id'])}")
                    self._polite_delay(base=2.0, jitter=1.5)

                    job_id_response = scrape_client.web_page_search(web_url=job_id_url)

                    if job_id_response.ok:
                        job_id_soup = BeautifulSoup(job_id_response.text, "html.parser")
                        level_card = job_id_soup.select_one("ul.description__job-criteria-list li")
                        level = (
                            level_card.get_text(strip=True).replace("Seniority level", "").strip()
                            if level_card else None
                        )
                        descripcion_card = job_id_soup.select_one(
                            "div.description__text--rich div.show-more-less-html__markup"
                        )
                        description = (
                            descripcion_card.get_text(separator="\n", strip=True)
                            if descripcion_card else None
                        )

                        job["level"] = level
                        job["description"] = description

                    else:
                        logger.warning(f"Skipping job {job['id']} details: status={job_id_response.status_code}")
                except ScrapeClientError as e:
                    logger.warning(f"Skipping job {job['id']} details due to ScrapeClientError: {e}")

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            list(executor.map(_fetch_offers_details, jobs_lists))

        # Flatten the list of lists back into a single list using itertools.chain
        jobs = list(chain.from_iterable(jobs_lists))

        logger.info(f"[Details] Completed LinkedIn jobs details fetch: "
                    f"{COUNT_TOTAL} listings processed [title='{self.title}', location='{self.location}'].")
        return jobs
