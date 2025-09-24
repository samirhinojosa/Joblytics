import requests
from pydantic import BaseModel,Field
from typing import Annotated, Optional
from app.infrastructure.http.header_provider import RandomHeaderProvider

class HttpClient(BaseModel):
    
    job_search_url: Annotated[str, Field(min_length=1, description="Job search URL")]


    def fetch_job_search(
            self,
            job_search_url: Optional[str] = None
    ):
        
        url = (job_search_url or self.job_search_url)

        # Getting random header provider
        hp = RandomHeaderProvider().header()
        
        got_200 = False
        while not got_200:
            response = requests.get(url, headers=hp)
            got_200 = response.status_code == 200
        return response