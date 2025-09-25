import re
import requests
import math
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator, PrivateAttr
from typing import Annotated, Optional
from urllib.parse import urlencode, quote_plus
from bs4 import BeautifulSoup
from app.infrastructure.http.scrape_client import ScrapeClient
from app.domain.exceptions import NoOffersFoundError

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

    def generate_url(
            self,
            title: Optional[str] = None,
            location: Optional[str] = None,
            distance: Optional[int] = None,
            offset: Optional[int] = None,
            time_posted: Optional[TimePosted] = None, 
            remote_mode: Optional[RemoteMode] = None
    ) -> str: 
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

        return f"{BASE_URL}?{urlencode(params, quote_via=quote_plus)}"
    

    def number_of_offers(
            self,
            response: requests.Response
    ) -> int:
        
        # Getting the number of offers
        soup = BeautifulSoup(response.text, "html.parser")
        node = soup.select_one("span.results-context-header__job-count")
        count = int(re.sub(r"\D+", "", node.get_text(strip=True))) if node else 0

        return count
    
    def fetching_offers(
            self,
    ) -> list[dict]:
        
        url = self.generate_url()
        scrape_client = ScrapeClient(web_url=url)
        response = scrape_client.web_page_search()
        number_of_offers = self.number_of_offers(response)
        
        if number_of_offers > 0:
            print(number_of_offers)


            # Loop through each page job listing (10 job per page)
            # for i in range(0, number_of_offers, 10):

            pass

        else:
            raise NoOffersFoundError(
                title=self.title,
                location=self.location,
                distance=self.distance,
                time_posted=self.time_posted.value,
                remote_mode=self.remote_mode.value,
                url=self.generate_url()
            )

        
        return []
        
