from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from joblytics.domain.entities.job_offer import RawJobOffer
from joblytics.domain.repositories.raw_job_offer_repository import (
    RawJobOfferRepository,
)


# --- Shared orchestration contract (query filters) ---
# Provider-agnostic search filters. Concrete pipelines (e.g. LinkedIn) map
# these onto their own provider-specific query parameters.
class TimePosted(str, Enum):
    ALL = "all"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class WorkModality(str, Enum):
    ALL = "all"
    ONSITE = "onsite"
    HYBRID = "hybrid"
    REMOTE = "remote"


@dataclass(frozen=True)
class PipelineReport:
    provider: str
    produced: int
    loaded: int
    started_at: datetime
    finished_at: datetime
    sample_data: list[dict[str, Any]] = field(default_factory=list)
    errors: tuple[str, ...] = ()

    @property
    def duration(self) -> timedelta:
        return self.finished_at - self.started_at

    @property
    def human_duration(self) -> str:
        total_seconds = int(self.duration.total_seconds())
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes}m {seconds}s"


class BaseJobPipeline(ABC):
    """
    Template Method base class for Joblytics pipelines.

    Subclasses must implement:
      - extract_jobs(): create items (e.g., JobOffer) from a provider

    """

    def __init__(
        self,
        provider: str,
        title: str,
        location: str,
        time_posted: TimePosted,
        work_modality: WorkModality,
        repository: RawJobOfferRepository | None = None,
    ) -> None:
        self.provider = provider
        self.title = title
        self.location = location
        self.time_posted = time_posted
        self.work_modality = work_modality
        self.repository = repository
        self.logger = logging.getLogger("joblytics")
        self._errors: list[str] = []

    @abstractmethod
    def extract_jobs(self) -> list[RawJobOffer]:
        pass

    def _persist(self, raw_jobs: list[RawJobOffer]) -> int:
        """
        Persist raw job offers via the injected repository, if any.

        A failure here is logged and recorded but does not fail the pipeline
        run — the in-memory scrape result must still be returned even if the
        raw-storage write failed (e.g. a transient Snowflake outage).

        Args:
            raw_jobs (list[RawJobOffer]): Raw job offers produced by extract_jobs().

        Returns:
            int: Number of offers actually persisted (0 if no repository is
                configured or if persistence failed).
        """
        if self.repository is None or not raw_jobs:
            return 0

        try:
            loaded = self.repository.save_batch(raw_jobs)
            self.logger.info(f"💾 Saved {loaded}/{len(raw_jobs)} jobs to raw storage.")
            return loaded
        except Exception as e:
            error_msg = f"❌ Failed to persist raw job offers: {e}"
            self.logger.error(error_msg)
            self._errors.append(error_msg)
            return 0

    def _log_report(self, report: PipelineReport) -> None:
        self.logger.info(
            f"📊 Report from {report.provider.upper()}: "
            f"Offers found: {report.produced} | Offers loaded: {report.loaded} | "
            f"Time: {report.human_duration}"
        )

    def run(self) -> PipelineReport:
        started_at = datetime.now(timezone.utc)
        produced_count = 0
        loaded_count = 0
        sample: list[dict[str, Any]] = []

        try:
            self.logger.info("🚀 Initiating the extraction pipeline... ")
            raw_jobs = self.extract_jobs()
            produced_count = len(raw_jobs)

            if produced_count > 0:
                sample = [
                    job.model_dump() if hasattr(job, "model_dump") else dict(job)
                    for job in raw_jobs[:5]
                ]

            loaded_count = self._persist(raw_jobs)

            self.logger.info("✅ Process completed.")

        except Exception as e:
            error_msg = f"❌ Unexpected error in the pipeline : {e}"
            self.logger.error(error_msg)
            self._errors.append(error_msg)
            raise
        finally:
            finished_at = datetime.now(timezone.utc)

            # Generating the final report (Immutable)
            report = PipelineReport(
                provider=self.provider,
                produced=produced_count,
                loaded=loaded_count,  ## --> to modify
                sample_data=sample,
                started_at=started_at,
                finished_at=finished_at,
                errors=tuple(self._errors),
            )

            self._log_report(report)

        return report
