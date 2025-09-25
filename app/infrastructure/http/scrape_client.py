import time
import requests
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
from typing import Annotated, Optional
from app.infrastructure.http.header_provider import RandomHeaderProvider

class ScrapeClient(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )    
    
    # Setup parameters
    job_search_url: Annotated[str, Field(min_length=1, description="Job search URL")]
    timeout: float = 15.0
    max_retries: int = 3
    backoff_factor: float = 0.5 # 0.5, 1.0, 2.0

    # Dependencies
    header_provider: RandomHeaderProvider = Field(default_factory=RandomHeaderProvider)

    # Internal state
    _session: requests.Session = PrivateAttr(default_factory=requests.Session)

    def fetch_job_search(
            self,
            job_search_url: Optional[str] = None
    ) -> requests.Response:
        
        url = (job_search_url or self.job_search_url)
        last_exc: Exception | None = None

        for attempt in range(1, self.max_retries +1):
            try:
                header = self.header_provider.header()
                response = self._session.get(url, headers=header, timeout=self.timeout)

                if response.status_code == 200:
                    return response
                
                if response.status_code in (429, 500, 502, 503, 504):
                    time.sleep(self.backoff_factor * (2 ** (attempt - 1)))
                    continue

                response.raise_for_status()
                return response
            except requests.RequestException as e:
                last_exc = e
                time.sleep(self.backoff_factor * (2 ** (attempt - 1)))

        if last_exc:
            raise last_exc
        raise RuntimeError("fetch_job_search failed without sepcific exception")
        