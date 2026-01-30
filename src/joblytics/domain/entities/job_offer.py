from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from typing import Annotated
from datetime import datetime, timezone


# --- Domain's Enums ---
class WorkModality(str, Enum):
    ONSITE = "onsite"
    HYBRID = "hybrid"
    REMOTE = "remote"
    UNKNOWN = "unknown"


class ContractType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"  # short term e.g. (1 semester)
    APPRENTICESHIP = "apprenticeship"  #  longer term e.g. (1-3 years)
    TEMPORARY = "temporary"
    UNKNOWN = "unknown"


class Seniority(str, Enum):
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"
    EXECUTIVE = "executive"  # e.g. ("Director", "VP", etc.)
    UNKNOWN = "unknown"


# --- Canonical Data model ---
class JobOfferBase(BaseModel):
    """
    Canonical job offer entity (provider-agnostic).

    Providers must normalize their scraped data into this model.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    # Provenance / identity
    provider: Annotated[str, Field(min_length=1)]  # e.g. "linkedin", "indeed", "wttj"
    provider_job_id: Annotated[str, Field(min_length=1)]
    url: HttpUrl

    # Core fields
    title: Annotated[str, Field(min_length=1)]
    company: Annotated[str, Field(min_length=1)]
    location: str | None = None

    # Optional enrichment & metadata
    description: str | None = None
    scraped_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )  # when collected it

    @property
    def internal_id(self) -> str:
        """Unique internal ID to avoid duplicates in the database."""
        return f"{self.provider}:{self.provider_job_id}"


class RawJobOffer(JobOfferBase):
    # --- Raw provider attributes (keep as strings for now) ---
    raw_work_modality: str | None = None
    raw_contract_type: str | None = None
    raw_seniority: str | None = None
    raw_time_posted: str | None = None  # keep original text like "3 days ago"
    raw_description_html: str | None = None  # to keep the original formatting

    # Optional: useful for dedup + traceability
    search_title: str | None = None  # the query used (e.g. "Data Engineer")
    search_location: str | None = None  # the query location (e.g. "Paris")
    search_work_modality: str | None = None  # the query work modality (e.g. "Paris")
    search_time_posted: str | None = None  # the query work modality (e.g. "onsite")

    raw: dict[str, object] | None = None  # to save additional fields


class NormalizedJobOffer(JobOfferBase):
    # Normalization
    work_modality: WorkModality = WorkModality.UNKNOWN
    contract_type: ContractType = ContractType.UNKNOWN
    seniority: Seniority = Seniority.UNKNOWN

    # normalized enrichment
    time_posted: datetime | None = None  # published at

    # lineage
    parser_version: Annotated[str, Field(min_length=1)] = "v1"
    normalized_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
