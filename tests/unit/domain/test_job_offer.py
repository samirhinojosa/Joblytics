from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from joblytics.domain.entities.job_offer import (
    NormalizedJobOffer,
    RawJobOffer,
    Seniority,
    WorkModality,
)


def _minimal_kwargs() -> dict:
    return {
        "provider": "linkedin",
        "provider_job_id": "123",
        "url": "https://www.linkedin.com/jobs/view/123",
        "title": "Data Engineer",
        "company": "Acme",
    }


def test_internal_id_composes_provider_and_job_id() -> None:
    offer = RawJobOffer(**_minimal_kwargs())
    assert offer.internal_id == "linkedin:123"


def test_raw_job_offer_defaults() -> None:
    offer = RawJobOffer(**_minimal_kwargs())
    assert offer.location is None
    assert offer.raw_work_modality is None
    assert isinstance(offer.scraped_at, datetime)
    assert offer.scraped_at.tzinfo is timezone.utc


def test_normalized_job_offer_defaults_to_unknown() -> None:
    offer = NormalizedJobOffer(**_minimal_kwargs())
    assert offer.work_modality == WorkModality.UNKNOWN
    assert offer.seniority == Seniority.UNKNOWN
    assert offer.parser_version == "v1"


def test_job_offer_is_frozen() -> None:
    offer = RawJobOffer(**_minimal_kwargs())
    with pytest.raises(ValidationError):
        offer.title = "Something else"


def test_job_offer_forbids_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        RawJobOffer(**_minimal_kwargs(), unexpected_field="nope")  # type: ignore[call-arg]


def test_job_offer_requires_valid_url() -> None:
    kwargs = _minimal_kwargs()
    kwargs["url"] = "not-a-url"
    with pytest.raises(ValidationError):
        RawJobOffer(**kwargs)


@pytest.mark.parametrize("field", ["provider", "provider_job_id", "title", "company"])
def test_job_offer_rejects_empty_required_strings(field: str) -> None:
    kwargs = _minimal_kwargs()
    kwargs[field] = ""
    with pytest.raises(ValidationError):
        RawJobOffer(**kwargs)
