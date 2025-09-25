from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Annotated, Optional
from urllib.parse import urlencode, quote_plus
from bs4 import BeautifulSoup

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
            time_posted: Optional[TimePosted] = None, 
            remote_mode: Optional[RemoteMode] = None
    ) -> str: 
        """
        Generate the Linkedin job search URL using the model values (and allowing for occasional overrides)
        """

        BASE_URL = "https://www.linkedin.com/jobs/search"

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

        return f"{BASE_URL}?{urlencode(params, quote_via=quote_plus)}"
