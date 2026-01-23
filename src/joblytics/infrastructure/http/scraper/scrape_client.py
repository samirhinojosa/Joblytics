import time
import random
import requests
import logging
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, HttpUrl, model_validator
from typing import Annotated, Optional, cast
from joblytics.core.config.settings import get_settings, Settings
from joblytics.infrastructure.http.robots import is_allowed
from joblytics.infrastructure.http.header_provider import RandomHeaderProvider
from joblytics.infrastructure.http.scraper.scrape_client_error import (
    ScrapeClientError,
)


logger = logging.getLogger("joblytics")

RETRY_STATUSES = {429, 500, 502, 503, 504, 999}


class ScrapeClient(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Setup parameters
    web_url: Annotated[HttpUrl, Field(description="Job search URL")]
    timeout: tuple[float, float] = (5.0, 15.0)  # (connect, read)
    max_retries: int = 3
    backoff_factor: float = 2.0  # 0.5, 1.0, 2.0
    backoff_cap: float = 30.0  # maximum backoff time

    # Compliance
    rate_limit_per_second: float | None = None
    jitter_seconds_min: float | None = None
    jitter_seconds_max: float | None = None
    respect_robots: bool | None = None
    dry_run: bool | None = None

    # Dependencies
    header_provider: RandomHeaderProvider = Field(default_factory=RandomHeaderProvider)

    # Internal state
    _session: requests.Session = PrivateAttr(default_factory=requests.Session)

    settings: Settings = Field(default_factory=get_settings)

    @model_validator(mode="after")
    def _load_defaults_from_settings(self) -> "ScrapeClient":
        settings = self.settings

        # Timeouts / reliability (keep current defaults if explicitly set)
        if self.timeout == (5.0, 15.0):  # default tuple in your class
            self.timeout = settings.resolve_timeout()

        # Override retry/backoff from settings only if left as defaults
        if self.max_retries == 3:
            self.max_retries = settings.MAX_RETRIES
        if self.backoff_factor == 2.0:
            self.backoff_factor = settings.BACKOFF_FACTOR
        if self.backoff_cap == 30.0:
            self.backoff_cap = settings.BACKOFF_CAP

        # Compliance
        if self.rate_limit_per_second is None:
            self.rate_limit_per_second = settings.RATE_LIMIT_PER_SECOND
        if self.jitter_seconds_min is None:
            self.jitter_seconds_min = settings.JITTER_SECONDS_MIN
        if self.jitter_seconds_max is None:
            self.jitter_seconds_max = settings.JITTER_SECONDS_MAX
        if self.respect_robots is None:
            self.respect_robots = settings.RESPECT_ROBOTS
        if self.dry_run is None:
            self.dry_run = settings.DRY_RUN

        return self

    def _get_backoff_sleep(self, attempt: int) -> float:
        """
        Compute exponential backoff with jitter and cap
        """
        base = self.backoff_factor * (2 ** (attempt - 1))
        sleep = min(base, self.backoff_cap) + random.uniform(0, 0.5)
        return cast(float, sleep)

    def _throttle(self) -> None:
        rps = float(self.rate_limit_per_second or 0.0)
        if rps <= 0:
            return
        base_delay = 1.0 / rps
        jmin = float(self.jitter_seconds_min or 0.0)
        jmax = float(self.jitter_seconds_max or 0.0)
        jitter = random.uniform(jmin, jmax) if jmax > 0 else 0.0
        time.sleep(base_delay + jitter)

    def web_page_search(self, web_url: Optional[HttpUrl] = None) -> requests.Response:
        url = web_url or self.web_url
        response: Optional[requests.Response] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                # header = self.header_provider.header(url)

                # t0 = time.monotonic()
                # response = self._session.get(
                #     str(url), headers=header, timeout=self.timeout
                # )

                headers, ua = self.header_provider.header_bundle(url)

                logger.debug(
                    "Compliance flags: respect_robots=%s dry_run=%s",
                    self.respect_robots,
                    self.dry_run,
                )

                # robots enforcement (best-effort)
                if bool(self.respect_robots):
                    decision = is_allowed(str(url), ua)
                    if not decision.allowed:
                        logger.warning(f"Blocked by robots.txt: {url}")
                        dummy = requests.Response()
                        dummy.status_code = 204
                        dummy.url = str(url)
                        dummy._content = b""
                        return dummy

                # dry-run enforcement (no network)
                if bool(self.dry_run):
                    logger.info(f"[DRY-RUN] Skipping request: {url}")
                    dummy = requests.Response()
                    dummy.status_code = 204
                    dummy.url = str(url)
                    dummy._content = b""
                    return dummy

                # rate limiting / throttling
                self._throttle()

                t0 = time.monotonic()
                response = self._session.get(
                    str(url),
                    headers=headers,
                    timeout=self.timeout,
                )

                elapsed = time.monotonic() - t0

                logger.debug(
                    f"Get {url} attempt={attempt} status={response.status_code} elapsed={elapsed:.3f}"
                )

                if response.ok:
                    return response

                if response.status_code in RETRY_STATUSES:
                    if attempt < self.max_retries:
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

                    # Last attempt — no sleep; fall through to error handling below
                    response.raise_for_status()
                    return response

                # Non-retryable → raise the underlying HTTP error
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                status: Optional[int] = (
                    response.status_code if response is not None else None
                )

                if attempt < self.max_retries:
                    sleep = self._get_backoff_sleep(attempt)
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
