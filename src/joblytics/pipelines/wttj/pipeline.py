from __future__ import annotations
import logging
import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, TypeVar
from urllib.parse import urlparse

from pydantic import HttpUrl

from joblytics.pipelines.base import BaseJobPipeline

from joblytics.domain.entities.job_offer import RawJobOffer
from joblytics.domain.exceptions.errors import NoOffersFoundError

from .constants import (
    MAX_DETAIL_ENRICHMENT_WORKERS,
    MAX_SHARDS_SCANNED_PER_QUERY,
    WAF_CHALLENGE_STATUS_CODE,
)
from .models import WTTJConfig
from .client import WTTJClient
from .parser import WTTJParser


logger = logging.getLogger("joblytics")

T = TypeVar("T")

# WTTJ's AWS WAF Bot Control occasionally serves a non-XML/HTML challenge
# body under an HTTP 2xx status, for any endpoint (sitemap index, shards,
# detail pages alike) — a plain HTTP-level retry (ScrapeClient already
# retries on 429/5xx) doesn't catch that, since the status looks fine.
# _fetch_and_parse retries the whole fetch+parse round-trip instead.
FETCH_RETRY_ATTEMPTS = 2
FETCH_RETRY_DELAY_SECONDS = 2.0

# Diagnostic-only opt-in: set WTTJ_DEBUG_CAPTURE_DIR to a directory path to
# save the raw body of exhausted-retry shards/detail pages there for offline
# inspection (e.g. to tell a stale sitemap entry apart from a WAF challenge
# page). No-op when unset. Not a permanent config surface, so it's not on
# Settings.
_DEBUG_CAPTURE_DIR_ENV = "WTTJ_DEBUG_CAPTURE_DIR"


def _capture_debug_body(url: str, text: str, reason: str) -> None:
    """
    Save a skipped response body for offline inspection, if
    WTTJ_DEBUG_CAPTURE_DIR is set.

    Args:
        url (str): The request URL the body came from.
        text (str): The raw response body.
        reason (str): Short tag identifying why the body was captured
            (e.g. "shard_failed", "detail_no_job_posting").
    """
    raw_dir = os.environ.get(_DEBUG_CAPTURE_DIR_ENV)
    if not raw_dir:
        return

    debug_dir = Path(raw_dir)
    debug_dir.mkdir(parents=True, exist_ok=True)
    slug = urlparse(url).path.strip("/").replace("/", "_") or "index"
    filename = f"{reason}__{slug}__{uuid.uuid4().hex[:8]}.txt"
    (debug_dir / filename).write_text(text, encoding="utf-8")


def _fetch_and_parse(
    client: WTTJClient,
    url: HttpUrl,
    parse: Callable[[str], T],
    *,
    capture_reason: str,
    delay_between_attempts: bool,
) -> T | None:
    """
    Fetch a URL and parse its body, retrying a bounded number of times on
    transient failures (network errors, non-2xx responses, WAF_CHALLENGE_
    STATUS_CODE responses, or a response that fails to parse).

    WAF_CHALLENGE_STATUS_CODE (202) is treated as a failure even though
    `requests.Response.ok` considers it fine: it's AWS WAF Bot Control's
    documented challenge status for this site, and its body is never real
    job/sitemap content, so treating it as a legitimate empty result would
    silently under-report actual matches.

    A successful parse is returned immediately, even if the parsed value is
    "empty" (e.g. an empty list, or `{}`) — that is a legitimate result
    (nothing matched), not a transient failure, so it is not retried. The
    raw body is still captured (if WTTJ_DEBUG_CAPTURE_DIR is set) in both
    cases — exhausted retries and an empty-but-successful parse — tagged
    "<capture_reason>_exhausted" or "<capture_reason>_empty" respectively,
    to help tell a stale sitemap entry apart from a WAF challenge page.

    Args:
        client (WTTJClient): Client used to perform the request.
        url (HttpUrl): The URL to fetch.
        parse (Callable[[str], T]): Parses the response body into a result.
        capture_reason (str): Base tag used when saving a body via
            WTTJ_DEBUG_CAPTURE_DIR (see _capture_debug_body).
        delay_between_attempts (bool): Whether to sleep between attempts.
            Should be False when the client's own throttle is already
            active (it already paces requests), True otherwise (e.g. the
            pre-throttle discovery phase).

    Returns:
        T | None: The parsed result, or None if every attempt failed.
    """
    last_failed_text: str | None = None

    for attempt in range(1, FETCH_RETRY_ATTEMPTS + 1):
        try:
            response = client.request(url)
        except Exception as e:
            logger.warning(f"⚠️ Attempt {attempt}/{FETCH_RETRY_ATTEMPTS} for {url}: {e}")
        else:
            if not response.ok or response.status_code == WAF_CHALLENGE_STATUS_CODE:
                logger.warning(
                    f"⚠️ Attempt {attempt}/{FETCH_RETRY_ATTEMPTS} for {url}: "
                    f"HTTP {response.status_code}"
                )
                last_failed_text = response.text
            else:
                try:
                    result = parse(response.text)
                except Exception as e:
                    logger.warning(
                        f"⚠️ Attempt {attempt}/{FETCH_RETRY_ATTEMPTS} for {url}: "
                        f"parse failed: {e}"
                    )
                    last_failed_text = response.text
                else:
                    if not result:
                        _capture_debug_body(
                            str(url), response.text, f"{capture_reason}_empty"
                        )
                    return result

        if delay_between_attempts and attempt < FETCH_RETRY_ATTEMPTS:
            time.sleep(FETCH_RETRY_DELAY_SECONDS)

    if last_failed_text is not None:
        _capture_debug_body(str(url), last_failed_text, f"{capture_reason}_exhausted")
    return None


class WTTJPipeline(BaseJobPipeline):
    def extract_jobs(self) -> list[RawJobOffer]:
        """
        Executes the full WTTJ scraping lifecycle: sitemap discovery, slug
        filtering, and detail enrichment.

        Unlike LinkedIn's pipeline, there is no separate cheap-summary phase:
        WTTJ's search UI is client-side rendered and exposes no server-side
        filtered search endpoint reachable over plain HTTP, so discovery goes
        through WTTJ's public, unfiltered sitemap instead. Each candidate URL
        requires exactly one fetch, since its JSON-LD block already carries
        full job data (title, company, location, description, etc.) — there
        is nothing cheaper to fetch first, unlike LinkedIn's summary cards.

        This method follows a multi-step orchestration:
        1. Discovery: fetch the sitemap index and select job-listing shards.
        2. Candidate filtering: fetch shards (capped at
           MAX_SHARDS_SCANNED_PER_QUERY) and keep URLs whose slug matches the
           requested title/location (best-effort, not a real filtered search).
        3. Parallel enrichment: fetch each candidate detail page and parse its
           JobPosting JSON-LD block into a RawJobOffer.

        Every fetch+parse round-trip (index, shard, detail) is retried a
        bounded number of times via _fetch_and_parse, since WTTJ's WAF
        occasionally serves a non-parseable body under an HTTP 2xx status.

        Returns:
            list[RawJobOffer]: A list of validated job offer entities.

        Raises:
            NoOffersFoundError: If no candidate URLs match the query.
            RuntimeError: If the sitemap index can't be fetched/parsed at
                all after retries — there is nothing to discover from.
        """

        config = WTTJConfig(
            title=self.title,
            location=self.location,
            time_posted=self.time_posted,
            work_modality=self.work_modality,
        )
        client = WTTJClient(config, self.provider)
        parser = WTTJParser()

        logger.info(f"🔍 Searching WTTJ sitemap for: ({self.title}, {self.location}).")

        index_url = client.build_sitemap_index_url()
        shard_urls = _fetch_and_parse(
            client,
            index_url,
            parser.parse_sitemap_index,
            capture_reason="index",
            delay_between_attempts=True,
        )
        if shard_urls is None:
            raise RuntimeError(
                f"Failed to fetch/parse the WTTJ sitemap index after "
                f"{FETCH_RETRY_ATTEMPTS} attempts."
            )

        candidates: list[str] = []
        scanned = 0
        for shard_url in shard_urls:
            if scanned >= MAX_SHARDS_SCANNED_PER_QUERY:
                break

            urls = _fetch_and_parse(
                client,
                HttpUrl(shard_url),
                parser.parse_job_listing_urls,
                capture_reason="shard",
                delay_between_attempts=True,
            )
            if not urls:
                continue  # exhausted retries, or an empty shard — try the next one

            candidates.extend(
                parser.filter_candidate_urls(urls, self.title, self.location)
            )
            scanned += 1

        if not candidates:
            raise NoOffersFoundError(
                title=self.title,
                location=self.location,
                time_posted=self.time_posted.name.lower(),
                work_modality=self.work_modality.name.lower(),
                url=index_url,
            )

        logger.info(
            f"📋 Found {len(candidates)} candidate offer(s) across {scanned} sitemap "
            "shard(s). Fetching details in parallel..."
        )

        # Activate the throttle just before heavy requests (details)
        client.scrape_client.enable_throttle = True

        all_raw_offers: list[RawJobOffer] = []
        lock = threading.Lock()
        done = 0  # shared counter

        def _enrich_job(url: str) -> None:
            nonlocal done

            try:
                details = _fetch_and_parse(
                    client,
                    HttpUrl(url),
                    parser.parse_job_detail,
                    capture_reason="detail",
                    delay_between_attempts=False,  # ScrapeClient throttle already paces
                )
                if not details:
                    # Either every retry failed, or the page parsed fine but
                    # had no JobPosting block (e.g. a stale listing) — both
                    # are already captured (if configured) inside
                    # _fetch_and_parse, tagged _exhausted vs _empty.
                    return

                full_data: dict[str, Any] = {
                    **details,
                    "provider": self.provider,
                    "provider_job_id": urlparse(url).path.strip("/"),
                    "url": url,
                    "search_title": self.title,
                    "search_location": self.location,
                    "search_work_modality": self.work_modality.value,
                    "search_time_posted": self.time_posted.value,
                }

                offer = RawJobOffer(**full_data)

                with lock:
                    done += 1
                    all_raw_offers.append(offer)
            except Exception as e:
                logger.warning(f"⚠️ Failed to enrich WTTJ job {url}: {e}")

        with ThreadPoolExecutor(max_workers=MAX_DETAIL_ENRICHMENT_WORKERS) as executor:
            executor.map(_enrich_job, candidates)

        logger.info(
            f"✅ Successfully extracted {len(all_raw_offers)}/{len(candidates)} full "
            "job offers."
        )
        return all_raw_offers
