import time
import random
import requests
import logging
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, HttpUrl
from typing import Annotated, Optional, cast
from app.infrastructure.http.header_provider import RandomHeaderProvider
from app.infrastructure.http.scraper.scrape_client_error import ScrapeClientError


logger = logging.getLogger(__name__)

RETRY_STATUSES = {429, 500, 502, 503, 504, 999}


class ScrapeClient(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Setup parameters
    web_url: Annotated[HttpUrl, Field(description="Job search URL")]
    timeout: tuple[float, float] = (5.0, 15.0)  # (connect, read)
    max_retries: int = 3
    backoff_factor: float = 2.0  # 0.5, 1.0, 2.0
    backoff_cap: float = 30.0  # maximum backoff time

    # Dependencies
    header_provider: RandomHeaderProvider = Field(default_factory=RandomHeaderProvider)

    # Internal state
    _session: requests.Session = PrivateAttr(default_factory=requests.Session)

    def _get_backoff_sleep(self, attempt: int) -> float:
        """
        Compute exponential backoff with jitter and cap
        """
        base = self.backoff_factor * (2 ** (attempt - 1))
        sleep = min(base, self.backoff_cap) + random.uniform(0, 0.5)
        return cast(float, sleep)

    def web_page_search(self, web_url: Optional[HttpUrl] = None) -> requests.Response:
        url = web_url or self.web_url
        response: Optional[requests.Response] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                # header = self.header_provider.header()
                header = self.header_provider.header(url)

                t0 = time.monotonic()
                response = self._session.get(
                    str(url), headers=header, timeout=self.timeout
                )
                elapsed = time.monotonic() - t0

                logger.debug(
                    f"Get {url} attempt={attempt} status={response.status_code} elapsed={elapsed:.3f}"
                )

                if response.ok:
                    return response

                if response.status_code in RETRY_STATUSES:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        try:
                            sleep = float(retry_after)
                        except ValueError:
                            sleep = self._get_backoff_sleep(attempt)
                    else:
                        sleep = self._get_backoff_sleep(attempt)

                    logger.warning(
                        f"Retryable status {response.status_code} on {url} "
                        + f"(attempt {attempt}/{self.max_retries}) Sleeping {sleep:.2f}s"
                    )
                    time.sleep(sleep)
                    continue

                # No retryable → launch HTTP error
                response.raise_for_status()
                return response

            except requests.RequestException as e:
                status: Optional[int] = (
                    response.status_code if response is not None else None
                )
                sleep = self._get_backoff_sleep(attempt)

                if attempt < self.max_retries:
                    logger.warning(
                        f"RequestException on {url} (attempt {attempt}/{self.max_retries}) "
                        + f"{(e.__class__.__name__,)} (status code={status}). Sleeping {sleep:.2f}s"
                    )
                    time.sleep(sleep)
                    continue

                logger.error(
                    f"RequestException on {url} (attempt {attempt}/{self.max_retries}) "
                    + f"{(e.__class__.__name__,)} (status code={status}). No more retries."
                )
                raise ScrapeClientError(url, self.max_retries, attempt, status)

        status = response.status_code if response is not None else None
        raise ScrapeClientError(url, self.max_retries, attempt, status)
