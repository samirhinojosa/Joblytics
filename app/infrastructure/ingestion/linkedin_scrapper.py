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
from app.infrastructure.http.scraper.scrape_client import ScrapeClient
from app.domain.exceptions import NoOffersFoundError
from app.infrastructure.http.scraper.scrape_client_error import ScrapeClientError


logger = logging.getLogger(__name__)

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

class LinkedinScrapper(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    title: Annotated[str, Field(min_length=1, description="Job title")]
    location: Annotated[str, Field(min_length=1, description="Job location")]
    distance: Annotated[int, Field(ge=0, le=100, description="Search radius")] = 10
    time_posted: TimePosted = TimePosted.ALL
    remote_mode: RemoteMode = RemoteMode.ALL

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
        Generate the Linkedin job search URL using the model values (and allowing for occasional overrides)
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
            params["geoId"] = geo_id
            params["position"] = 1
            params["pageNum"] = 0
            params["start"] = offset
            # params["count"] = 25
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
    

    def generate_job_detail_url(self, job_id: int)-> HttpUrl: 
        """
        Generate a valid LinkedIn job detail URL for a given job ID.
        """        
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
        
        return HttpUrl(url)
    

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

    
    def fetching_offers(
            self,
    ) -> list[dict]:
        """
        Fetching the offers number
        """

        url = self.generate_jobs_url()
        scrape_client = ScrapeClient(web_url=url)
        logger.info(f"Fetching data from LinkedIn API...")
        response = scrape_client.web_page_search()
        number_of_offers = self.number_of_offers(response)
        geo_id = self._extract_geo_id(response)

        PAGE_SIZE = 10
        MAX_START = min(975, number_of_offers - 1)  # Avoiding to request empty webpages
        
        if number_of_offers > 0:

            if number_of_offers > 1000:
                logger.warning(f"Processing capped at 1,000 offers to avoid LinkedIn rate limits (total {number_of_offers})")

            jobs = []

            for i in range(0, MAX_START + 1, PAGE_SIZE):
                
                logger.info(f"Processing jobs offers batch {i}-{i + PAGE_SIZE} (total {number_of_offers})")
                            
                _url = self.generate_jobs_url(offset=i, geo_id=geo_id)
                response = scrape_client.web_page_search(web_url=_url)

                # Parse the HTML content of the response using BeautifulSoup
                soup = BeautifulSoup(response.text, "html.parser")

                # Find all list items (li) within the joblist, representing individual job postings
                soup_jobs = soup.find_all("li")

                for job in soup_jobs:   

                    level = None
                    description = None
                    
                    if not isinstance(job, Tag):
                        continue

                    job_id_card = job.select_one("div.base-card")
                    job_id = job_id_card["data-entity-urn"].split(":")[3] if job_id_card.has_attr("data-entity-urn") else None # type: ignore
                  
                    title_card = job.select_one("h3.base-search-card__title")
                    title = title_card.get_text(strip=True) if title_card else None        

                    company_card = job.select_one("h4.base-search-card__subtitle")
                    company = company_card.get_text(strip=True) if company_card else None

                    location_card = job.select_one("span.job-search-card__location")
                    location = location_card.get_text(strip=True) if location_card else None

                    url_card = job.select_one("a.base-card__full-link")
                    url = url_card.get("href") if url_card else None

                    logger.debug(f"Fetching job details [id={job_id}] - '{title}' - '{company}'")

                    if job_id:
                        job_id_url = self.generate_job_detail_url(int(job_id))

                        self._polite_delay(base=0.45, jitter=0.4)

                        try:
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
                            else:
                                logger.warning(f"Skipping job {job_id} detail: status={job_id_response.status_code}")
                        except ScrapeClientError as e:
                            logger.warning(f"Skipping job {job_id} detail due to ScrapeClientError: {e}")
                    

                    job_details = {
                        "id" : job_id,
                        "title" : title,
                        "level" : level,
                        "description" : description,
                        "company" : company,
                        "location" : location,
                        "url": url        
                    }

                    jobs.append(job_details)

            print(len(jobs))

        else:
            raise NoOffersFoundError(
                title=self.title,
                location=self.location,
                distance=self.distance,
                time_posted=self.time_posted.name.lower(),
                remote_mode=self.remote_mode.name.lower(),
                url=self.generate_jobs_url()
            )

        
        for job in jobs:
            print(f"title: {job["title"]}, id: {job["id"]}, company: {job["company"]}")

        # import pandas as pd
        # file_name = "jobs.csv"

        return []
        
