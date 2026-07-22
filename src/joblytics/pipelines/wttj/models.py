from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Annotated

from joblytics.pipelines.base import TimePosted, WorkModality


class WTTJConfig(BaseModel):
    """
    Validated search configuration for the Welcome to the Jungle scraper.

    Unlike LinkedInConfig, `time_posted` and `work_modality` are not mapped
    onto URL query parameters: WTTJ's search UI is client-side rendered and
    exposes no server-filtered search endpoint, so discovery goes through an
    unfiltered public sitemap (see pipelines/wttj/pipeline.py) with title and
    location matched against each candidate URL's slug. `time_posted` and
    `work_modality` are kept here for CLI/BaseJobPipeline parity and are
    echoed onto RawJobOffer for traceability, but are not applied as filters
    in this Raw-layer-only implementation.
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    title: Annotated[str, Field(min_length=1, description="Job title")]
    location: Annotated[str, Field(min_length=1, description="Job location")]
    time_posted: TimePosted = TimePosted.ALL
    work_modality: WorkModality = WorkModality.ALL

    @field_validator("title", "location")
    @classmethod
    def _strip_whitespace(cls, v: str) -> str:
        """Clean up unnecessary blank spaces."""
        return v.strip()
