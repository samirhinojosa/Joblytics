from __future__ import annotations
import logging
from joblytics.pipelines.base import BaseJobPipeline

from joblytics.pipelines.linkedin_scrapper import (
    LinkedInScrapper,
    TimePosted,
    WorkModality,
)
from joblytics.domain.entities.job_offer import RawJobOffer
from joblytics.domain.exceptions.errors import NoOffersFoundError


logger = logging.getLogger("joblytics")


class LinkedinInScraperXX(BaseJobPipeline):
    def extract_jobs(self) -> list[RawJobOffer]:
        scrapper = LinkedInScrapper(
            provider=self.provider,
            title=self.title,
            location=self.location,
            time_posted=self.time_posted,
            work_modality=self.work_modality,
        )

        jobs_summary = scrapper.fetch_offers_summary() or []

        # def extract_jobs(self) -> list[RawJobOffer]:
        #     scrapper = LinkedInScrapper(...)

        #     jobs_summary = scrapper.fetch_offers_summary() or []

        #     if not jobs_summary:
        #         # Lanzamos la excepción específica aquí
        #         raise NoOffersFoundError(
        #             f"No se encontraron ofertas para '{self.title}' en '{self.location}'"
        #         )

        #     offers = scrapper.fetch_offers_details(jobs_summary)
        #     return offers or []

        offers = scrapper.fetch_offers_details(jobs_summary)
        #     if not offers:
        #         raise NoOffersFoundError(title=self.title, )

        # except NoOffersFoundError as e:
        #     logger.warning(str(e))
        #     typer.secho(f"No offers found. Info: {e}. Exiting.", fg=typer.colors.YELLOW)
        #     raise typer.Exit(code=0)

        jobs_details = [offer.model_dump() for offer in (offers or [])]

        if not jobs_details:
            logger.warning("No job details fetched.")
        logger.debug(f"Fetched job details: {len(jobs_details)}")
        logger.info("LinkedIn scrape finished successfully")
        return offers
