from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Annotated


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


class LinkedInConfig(BaseModel):
    """
    Validated search configuration for the LinkedIn scraper.
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    title: Annotated[str, Field(min_length=1, description="Job title")]
    location: Annotated[str, Field(min_length=1, description="Job location")]
    distance: Annotated[int, Field(ge=0, le=100, description="Search radius")] = 10
    time_posted: TimePosted = TimePosted.ALL
    work_modality: WorkModality = WorkModality.ALL

    # Technical scraper configuration
    PAGE_SIZE: int = 10
    MAX_RESULTS: int = 1000

    @field_validator("title", "location")
    @classmethod
    def _strip_whitespace(cls, v: str) -> str:
        """Clean up unnecessary blank spaces."""
        return v.strip()

    @property
    def time_posted_value(self) -> str:
        """Map the Enum to the value that the LinkedIn URL understands."""
        mapping = {
            TimePosted.ALL: "",
            TimePosted.DAY: "r86400",
            TimePosted.WEEK: "r604800",
            TimePosted.MONTH: "r2592000",
        }
        return mapping[self.time_posted]

    @property
    def work_modality_value(self) -> str:
        """Map the Enum to the value that the LinkedIn URL understands."""
        mapping = {
            WorkModality.ALL: "",
            WorkModality.ONSITE: "1",
            WorkModality.HYBRID: "2",
            WorkModality.REMOTE: "3",
        }
        return mapping[self.work_modality]
