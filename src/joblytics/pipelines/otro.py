from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Generic, Sequence, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class PipelineReport:
    provider: str
    produced: int
    loaded: int
    started_at: datetime
    finished_at: datetime
    errors: tuple[str, ...] = ()


class BasePipeline(ABC, Generic[T]):
    """
    Template Method base class for Joblytics pipelines.

    Subclasses must implement:
      - produce(): create items (e.g., JobOffer) from a provider
      - load(): persist items and return number of stored records

    Optional hooks:
      - validate(): filter/validate items before persisting
      - post_run(): side effects after a run (metrics, logs, artifacts)
      - on_error(): custom error handling
    """

    provider: str

    def run(self) -> PipelineReport:
        started_at = datetime.now(timezone.utc)
        errors: list[str] = []
        produced_count = 0
        loaded_count = 0

        try:
            items = list(self.produce())
            produced_count = len(items)

            items = list(self.validate(items))
            loaded_count = self.load(items)

            self.post_run(items=items, report=None)
        except Exception as exc:  # noqa: BLE001 (framework boundary)
            errors.append(f"{type(exc).__name__}: {exc}")
            self.on_error(exc)
        finally:
            finished_at = datetime.now(timezone.utc)

        report = PipelineReport(
            provider=self.provider,
            produced=produced_count,
            loaded=loaded_count,
            started_at=started_at,
            finished_at=finished_at,
            errors=tuple(errors),
        )

        # Provide report to post_run after it's built
        if not report.errors:
            self.post_run(items=None, report=report)

        return report

    @abstractmethod
    def produce(self) -> Sequence[T] | list[T]:
        """Create items from a provider (e.g., JobOffer)."""

    def validate(self, items: Sequence[T]) -> Sequence[T]:
        """Optional hook: validate/filter items before persisting."""
        return items

    @abstractmethod
    def load(self, items: Sequence[T]) -> int:
        """Persist items and return number of stored records."""

    def post_run(self, items: Sequence[T] | None, report: PipelineReport | None) -> None:
        """Optional hook: metrics/logging/artifacts."""
        return

    def on_error(self, exc: Exception) -> None:
        """Optional hook: custom error handling."""
        return
