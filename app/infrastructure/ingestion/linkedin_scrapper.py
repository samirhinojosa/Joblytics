import re
import requests
import math
from enum import Enum
import logging
import time
from pydantic import BaseModel, ConfigDict, Field, field_validator, PrivateAttr, HttpUrl
from typing import Annotated, Optional
from urllib.parse import urlencode, quote_plus
from bs4 import BeautifulSoup, Tag
from app.infrastructure.http.scraper.scrape_client import ScrapeClient
from app.domain.exceptions import NoOffersFoundError


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
            params["position"] = 1
            params["pageNum"] = 0
            params["start"] = offset
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
    
    def generate_jod_detail_url(self, job_id: int)-> HttpUrl: 
        
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
        
        return HttpUrl(url)

    
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

        PAGE_SIZE = 25
        MAX_START = 975  # Last valid start
        
        if number_of_offers > 0:

            if number_of_offers > MAX_START:
                logger.warning(f"Processing capped at 1,000 offers to avoid LinkedIn rate limits (total {number_of_offers})")

            jobs = []

            for i in range(0, MAX_START + 1, PAGE_SIZE):
                
                logger.info(f"Processing jobs offers batch {i}-{i + PAGE_SIZE} (total {number_of_offers})")
                            
                _url = self.generate_jobs_url(offset=i)
                response = scrape_client.web_page_search(web_url=_url)

                # Parse the HTML content of the response using BeautifulSoup
                soup = BeautifulSoup(response.text, "html.parser")

                # Find all list items (li) within the joblist, representing individual job postings
                soup_jobs = soup.find_all("li")

                counter = 1
                for job in soup_jobs:   

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

                    logger.info(f"Processing job details {counter}")
                    if job_id:
                        job_id_url = self.generate_jod_detail_url(int(job_id))

                        if (counter % 5) == 0:
                            time.sleep(0.5)

                        job_id_response = scrape_client.web_page_search(web_url=job_id_url)
                        job_id_soup = BeautifulSoup(job_id_response.text, "html.parser")

                        level_card = job_id_soup.select_one("ul.description__job-criteria-list li")
                        level = (
                            level_card.get_text(strip=True).replace("Seniority level", "").strip() 
                            if level_card else None 
                        )  
                    

                    job_details = {
                        "id" : job_id,
                        "title" : title,
                        "level" : level if level else None,
                        "company" : company,
                        "location" : location,
                        "url": url        
                    }

                    jobs.append(job_details)
                    counter += 1

                    # print(f"{job_id}, {title}, {level}, {company}, {location}, {url}")
            print(jobs)
                    
        else:
            raise NoOffersFoundError(
                title=self.title,
                location=self.location,
                distance=self.distance,
                time_posted=self.time_posted.name.lower(),
                remote_mode=self.remote_mode.name.lower(),
                url=self.generate_jobs_url()
            )

        
        return []
        
