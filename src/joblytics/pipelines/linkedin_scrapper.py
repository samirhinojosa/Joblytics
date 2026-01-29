import re
import requests
from enum import Enum
import logging
import time
import random
from pydantic import BaseModel, ConfigDict, Field, field_validator, HttpUrl
from typing import Annotated, Optional
from urllib.parse import urlencode, quote_plus
from bs4 import BeautifulSoup, Tag
from itertools import zip_longest
from concurrent.futures import ThreadPoolExecutor
import threading
from joblytics.infrastructure.http.scraping.http_client import ScrapeClient
from joblytics.domain.exceptions.errors import NoOffersFoundError
from joblytics.infrastructure.http.scraping.errors import (
    ScrapeClientError,
)
from joblytics.domain.entities.job_offer import RawJobOffer


logger = logging.getLogger("joblytics")


class TimePosted(str, Enum):
    ALL = "all"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


TIME_POSTED_TO_LINKEDIN = {
    TimePosted.ALL: "",
    TimePosted.DAY: "r86400",
    TimePosted.WEEK: "r604800",
    TimePosted.MONTH: "r2592000",
}


class WorkModality(str, Enum):
    ALL = "all"
    ONSITE = "onsite"
    HYBRID = "hybrid"
    REMOTE = "remote"


WORK_MODALITY_TO_LINKEDIN = {
    WorkModality.ALL: "",
    WorkModality.ONSITE: "1",
    WorkModality.HYBRID: "2",
    WorkModality.REMOTE: "3",
}


class LinkedInScrapper(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Annotated[str, Field(min_length=1, description="Job title")]
    location: Annotated[str, Field(min_length=1, description="Job location")]
    distance: Annotated[int, Field(ge=0, le=100, description="Search radius")] = 10
    time_posted: TimePosted = TimePosted.ALL
    work_modality: WorkModality = WorkModality.ALL
    provider: str = "linkedin"

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
        work_modality: Optional[WorkModality] = None,
    ) -> HttpUrl:
        """Generate the LinkedIn job search URL using the model values (and allowing for occasional overrides)

        Args:
            title (Optional[str]): Job title override. If None, uses the model title.
            location (Optional[str]): Job location override. If None, uses the model location.
            distance (Optional[int]): Search radius override in km. If None, uses the model distance.
            geo_id (Optional[int]): LinkedIn geoId to restrict the search area.
            offset (Optional[int]): Pagination offset for job listings.
            time_posted (Optional[TimePosted]): Filter by time posted. If None, uses the model value.
            work_modality (Optional[WorkModality]): Onsite / hybrid / remote filter. If None, uses the model value.

        Returns:
            HttpUrl: Fully built LinkedIn job search URL.
        """
        params = {
            "keywords": (title or self.title),
            "location": (location or self.location),
            "distance": (distance if distance is not None else self.distance),
        }

        tp_enum = time_posted or self.time_posted
        tp = TIME_POSTED_TO_LINKEDIN[tp_enum]
        if tp:
            params["f_TPR"] = tp

        rm_enum = work_modality or self.work_modality
        rm = WORK_MODALITY_TO_LINKEDIN[rm_enum]
        if rm:
            params["f_WT"] = rm

        if offset is not None:
            BASE_URL = (
                "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            )
            if geo_id is not None:
                params["geoId"] = geo_id
            params["position"] = 1
            params["pageNum"] = 0
            params["start"] = offset
            params["count"] = self.PAGE_SIZE
        else:
            BASE_URL = "https://www.linkedin.com/jobs/search"

        return HttpUrl(f"{BASE_URL}?{urlencode(params, quote_via=quote_plus)}")

    def number_of_offers(self, response: requests.Response) -> int:
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

            val = node.get("value")
            geo_id = val.strip() if isinstance(val, str) else ""
            if geo_id.isdigit():
                return int(geo_id)
            else:
                logger.debug(f"geoId found but invalid: {geo_id}")
                return None
        except Exception as e:
            logger.warning(f"Failed to extract geoId: {e}")
            return None

    def _polite_delay(self, base: float = 0.6, jitter: float = 0.5) -> None:
        """
        Short pause with jitter to avoid sending a lot of requests to the detail endpoint.
        """
        time.sleep(base + random.random() * jitter)

    def fetch_offers_summary(
        self,
    ) -> list[RawJobOffer]:
        """
        Goes through the pagination of the LinkedIn jobs listings and return an offers basic list
        """
        try:
            logger.info(
                f"[Summary] Starting LinkedIn jobs listings fetch: [title='{self.title}', location='{self.location}', "
                f"time_posted='{self.time_posted.name.lower()}', work_modality='{self.work_modality.name.lower()}']"
            )

            url = self.generate_jobs_url()

            # NOTE:
            # In this execution path we are not using parallel threads and requests are performed
            # sequentially while iterating over job offer lists. Therefore, throttling can be safely
            # disabled here to avoid unnecessary artificial delays and improve throughput.
            scrape_client = ScrapeClient(
                provider=self.provider, web_url=url, enable_throttle=False
            )
            response = scrape_client.web_page_search()
            number_of_offers = self.number_of_offers(response)
            geo_id = self._extract_geo_id(response)

            MAX_START = min(
                975, number_of_offers - 1
            )  # Avoiding to request empty webpages

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
                    work_modality=self.work_modality.name.lower(),
                    url=self.generate_jobs_url(),
                )

            if number_of_offers > 1000:
                logger.warning(
                    f"[Summary] Processing capped at 1,000 offers to avoid LinkedIn rate limits (total {number_of_offers})"
                )

            jobs_summary: list[RawJobOffer] = []
            for i in range(0, MAX_START + 1, self.PAGE_SIZE):
                if random.random() < 0.6:  # print with 60% probability
                    logger.info(
                        f"[Summary] Fetching batch {i}-{i + self.PAGE_SIZE} of {number_of_offers} job listings..."
                    )

                _url = self.generate_jobs_url(offset=i, geo_id=geo_id)
                self._polite_delay(base=0.45, jitter=0.4)
                response = scrape_client.web_page_search(web_url=_url)
                soup = BeautifulSoup(response.text, "html.parser")
                # soup_jobs = soup.find_all("li")

                soup_jobs = [li for li in soup.find_all("li") if isinstance(li, Tag)]

                for job in soup_jobs:
                    card = job.select_one("[data-entity-urn]")
                    if not card:
                        continue

                    raw_urn = card.get("data-entity-urn")
                    if not isinstance(raw_urn, str):
                        continue

                    job_id = raw_urn.split(":")[-1]

                    title = job.select_one("h3") or job.select_one(
                        ".base-search-card__title"
                    )
                    title = title.get_text(strip=True)

                    company = job.select_one("h4") or job.select_one(
                        ".base-search-card__subtitle"
                    )
                    company = company.get_text(strip=True)

                    location = job.select_one(".job-search-card__location")
                    location = location.get_text(strip=True)

                    url_node = job.select_one("a.base-card__full-link")
                    clean_url = str(url_node.get("href", "")).split("?")[0]

                    modality_node = job.select_one(
                        ".base-search-card__metadata"
                    ) or job.select_one(".job-search-card__metadata")
                    raw_work_modality = "On-site"  # Default

                    if modality_node:
                        modality_text = modality_node.get_text(strip=True).lower()
                        if "remote" in modality_text:
                            raw_work_modality = "Remote"
                        elif "hybrid" in modality_text:
                            raw_work_modality = "Hybrid"

                    if not (title and company and url_node):
                        continue

                    try:
                        offer = RawJobOffer(
                            provider=self.provider,
                            provider_job_id=job_id,
                            url=HttpUrl(clean_url),
                            title=title,
                            company=company,
                            location=location,
                            raw_work_modality=raw_work_modality,
                            search_title=self.title,
                            search_location=self.location,
                            search_work_modality=self.work_modality.name.lower(),
                            search_time_posted=self.time_posted.name.lower(),
                        )
                        jobs_summary.append(offer)
                    except Exception as e:
                        logger.warning(
                            f"Unexpected error while fetching offer {job_id}: {e}"
                        )

            logger.info(
                f"[Summary] Completed LinkedIn job summary fetch: {len(jobs_summary)}/{number_of_offers} "
                f"listings retrieved [title='{self.title}', location='{self.location}', "
                f"time_posted='{self.time_posted.name.lower()}', work_modality='{self.work_modality.name.lower()}']."
            )
            return jobs_summary

        except NoOffersFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error while fetching LinkedIn offers summary: {type(e).__name__} - {e}"
            )
            return []

    def fetch_offers_details(self, jobs: list[RawJobOffer]) -> list[RawJobOffer] | None:
        if not jobs:
            return None

        COUNT_TOTAL = len(jobs)
        logger.info(
            f"[Details] Starting LinkedIn jobs details fetch: {COUNT_TOTAL} listings to process."
        )

        MAX_WORKERS = 5
        BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/"

        # NOTE:
        # Split the list into chunks of 5 dictionaries each using zip_longest
        # (fills missing values with None and filters them out)
        jobs_chunks = [
            list(filter(None, chunk))
            for chunk in zip_longest(*[iter(jobs)] * MAX_WORKERS)
        ]

        enriched_jobs: list[RawJobOffer] = []

        # shared counter
        done = 0
        lock = threading.Lock()

        def _fetch_chunk_details(chunk: list[RawJobOffer]) -> None:
            nonlocal done

            scrape_client = ScrapeClient(
                provider=self.provider,
                web_url=HttpUrl(BASE_URL),
            )

            for job in chunk:
                try:
                    with lock:
                        done += 1

                    if random.random() < 0.4:  # print with 40% probability
                        logger.info(
                            f"[Details] Fetching jobs details {done}/{COUNT_TOTAL} (id={job.provider_job_id})"
                        )

                    job_id_url = HttpUrl(f"{BASE_URL}{job.provider_job_id}")
                    self._polite_delay(base=2.0, jitter=1.5)

                    response = scrape_client.web_page_search(web_url=job_id_url)

                    if response.ok:
                        soup = BeautifulSoup(response.text, "html.parser")

                        raw_contract_type = None
                        raw_seniority = None
                        for li in soup.select(
                            "ul.description__job-criteria-list li.description__job-criteria-item"
                        ):
                            label_node = li.select_one(
                                ".description__job-criteria-subheader"
                            )
                            value_node = li.select_one(
                                ".description__job-criteria-text.description__job-criteria-text--criteria"
                            ) or li.select_one(".description__job-criteria-text")

                            if not label_node or not value_node:
                                continue

                            if label_node.get_text(strip=True) == "Seniority level":
                                raw_seniority = value_node.get_text(strip=True)

                            if label_node.get_text(strip=True) == "Employment type":
                                raw_contract_type = value_node.get_text(strip=True)

                        raw_time_posted = soup.select_one(".posted-time-ago__text")
                        if raw_time_posted:
                            raw_time_posted = raw_time_posted.get_text(strip=True)

                        desc_node = soup.select_one(
                            "div.description__text--rich div.show-more-less-html__markup"
                        )
                        description = (
                            desc_node.get_text(separator="\n", strip=True)
                            if desc_node
                            else None
                        )
                        raw_description_html = str(desc_node) if desc_node else None

                        updated_job = job.model_copy(
                            update={
                                "description": description,
                                "raw_seniority": raw_seniority,
                                "raw_contract_type": raw_contract_type,
                                "raw_time_posted": raw_time_posted,
                                "raw_description_html": raw_description_html,
                            }
                        )

                        with lock:
                            enriched_jobs.append(updated_job)

                    else:
                        logger.warning(
                            f"Skipping job {job.provider_job_id} details: status={response.status_code}"
                        )
                except ScrapeClientError as e:
                    logger.warning(
                        f"Skipping job {job.provider_job_id} details due to ScrapeClientError: {e}"
                    )

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            list(executor.map(_fetch_chunk_details, jobs_chunks))

        # Flatten the list of lists back into a single list using itertools.chain
        # jobs = list(chain.from_iterable(jobs_lists))

        logger.info(
            f"[Details] Completed LinkedIn jobs details fetch: "
            f"{COUNT_TOTAL} listings processed [title='{self.title}', location='{self.location}']."
        )
        return enriched_jobs
