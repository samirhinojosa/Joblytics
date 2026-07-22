from typing import Sequence

from pydantic import HttpUrl

from joblytics.domain.entities.job_offer import RawJobOffer
from joblytics.domain.repositories.raw_job_offer_repository import (
    RawJobOfferRepository,
)


def _offer(job_id: str) -> RawJobOffer:
    return RawJobOffer(
        provider="linkedin",
        provider_job_id=job_id,
        url=HttpUrl("https://www.linkedin.com/jobs/view/" + job_id),
        title="Data Engineer",
        company="Acme",
    )


class _FakeRepository:
    def __init__(self) -> None:
        self.saved: list[RawJobOffer] = []

    def save_batch(self, offers: Sequence[RawJobOffer]) -> int:
        self.saved.extend(offers)
        return len(offers)


def test_fake_repository_satisfies_protocol() -> None:
    repository: RawJobOfferRepository = _FakeRepository()

    loaded = repository.save_batch([_offer("1"), _offer("2")])

    assert loaded == 2
    assert len(repository.saved) == 2  # type: ignore[attr-defined]
