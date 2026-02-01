from __future__ import annotations
import logging
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from joblytics.pipelines.base import BaseJobPipeline

from joblytics.domain.entities.job_offer import RawJobOffer
from joblytics.domain.exceptions.errors import NoOffersFoundError

from .models import LinkedInConfig
from .client import LinkedInClient
from .parser import LinkedInParser


logger = logging.getLogger("joblytics")


class LinkedInPipeline(BaseJobPipeline):
    def extract_jobs(self) -> list[RawJobOffer]:
        """
        Executes the full LinkedIn scraping lifecycle: search, discovery, and enrichment.

        This method follows a multi-step orchestration:
        1. Discovery: Performs an initial search to retrieve the total job count
           and the provider-specific geographic identifier (geoId).
        2. Summary Fetching: Iterates through LinkedIn search results pages to
           collect basic job metadata (IDs, titles, companies).
        3. Parallel Enrichment: Utilizes a ThreadPoolExecutor to fetch the full
           descriptions and specific criteria (seniority, contract type) for each
           job offer concurrently.
        4. Validation: Each raw data point is transformed and validated into a
           RawJobOffer domain entity.

        Returns:
            list[RawJobOffer]: A list of validated job offer entities containing
                complete information (summary + rich details).

        Raises:
            NoOffersFoundError: If the search returns zero results or if job
                summaries cannot be parsed from the HTML.
            ScrapeClientError: If there is a persistent network or provider failure.
        """

        config = LinkedInConfig(
            title=self.title,
            location=self.location,
            time_posted=self.time_posted,
            work_modality=self.work_modality,
        )
        client = LinkedInClient(config, self.provider)
        parser = LinkedInParser()

        # Initial search and GeoID
        logger.info(
            f"🔍 Searching for: ({self.title}, {self.location}, {self.time_posted.value.lower()}, {self.work_modality.value.lower()})."
        )
        initial_url = client.build_search_url()
        initial_html = client.request(initial_url).text
        total_offers = parser.parse_job_count(initial_html)
        geo_id = parser.parse_geo_id(initial_html)

        if total_offers == 0:
            raise NoOffersFoundError(
                title=self.title,
                location=self.location,
                # distance=self.distance,
                time_posted=self.time_posted.name.lower(),
                work_modality=self.work_modality.name.lower(),
                url=initial_url,
            )

        logger.info(
            f"📊 Found approximately {total_offers} offers. Fetching summaries..."
        )

        # Avoiding to request empty webpages
        max_start = min(975, total_offers - 1)

        # Get Summaries (Pagination)
        summaries: list[dict[str, Any]] = []
        for offset in range(0, max_start + 1, config.PAGE_SIZE):
            if random.random() < 0.9:  # print with 60% probability
                logger.info(
                    f"[Summary] Fetching Summaries batch {offset}-{offset + config.PAGE_SIZE} of {total_offers} job listings..."
                )
            search_url = client.build_search_url(offset=offset, geo_id=geo_id)
            page_html = client.request(search_url).text
            cards = parser.parse_summary_cards(page_html)
            summaries.extend(cards)

        if not summaries:
            raise NoOffersFoundError(
                title=self.title,
                location=self.location,
                # distance=self.distance,
                time_posted=self.time_posted.name.lower(),
                work_modality=self.work_modality.name.lower(),
                url=initial_url,
            )

        logger.info(
            f"[Summary] 📋 Collected {len(summaries)} summaries. Fetching full details in parallel..."
        )

        # Activate the throttle just before heavy requests (details)
        client.scrape_client.enable_throttle = True

        all_raw_offers: list[RawJobOffer] = []
        lock = threading.Lock()
        done = 0  # shared counter

        # Get details (Parallel enrichment)
        def _enrich_job(summary_data: dict[str, Any]):
            nonlocal done

            try:
                detail_url = client.build_detail_url(summary_data["provider_job_id"])
                response = client.request(detail_url)

                if response.ok:
                    details = parser.parse_job_details(response.text)
                    # Combine summary + details + required metadata
                    full_data: dict[str, Any] = {
                        **summary_data,
                        **details,
                        "provider": self.provider,
                        "search_title": self.title,
                        "search_location": self.location,
                    }

                    offer = RawJobOffer(**full_data)

                    with lock:
                        done += 1
                        all_raw_offers.append(offer)

                        if random.random() < 0.4:  # print with 40% probability
                            logger.info(
                                f"[Details] Processing {done}/{len(summaries)} jobs..."
                            )
            except Exception as e:
                logger.warning(
                    f"⚠️ Failed to enrich job {summary_data.get('provider_job_id')}: {e}"
                )

        # Concurrent execution
        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(_enrich_job, summaries)

        logger.info(
            f"✅ Successfully extracted {len(all_raw_offers)}/{len(summaries)} full job offers."
        )
        return all_raw_offers
