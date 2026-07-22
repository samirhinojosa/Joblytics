from __future__ import annotations

from typing import Protocol, Sequence

from joblytics.domain.entities.job_offer import RawJobOffer


class RawJobOfferRepository(Protocol):
    """Port for persisting raw, unmodified job offers (Bronze/RAW layer)."""

    def save_batch(self, offers: Sequence[RawJobOffer]) -> int:
        """
        Persist a batch of raw job offers exactly as scraped.

        Args:
            offers (Sequence[RawJobOffer]): Validated raw job offers to persist.

        Returns:
            int: Number of offers actually persisted.

        Raises:
            RuntimeError: Implementation-specific failure while persisting the batch.
        """
        ...
