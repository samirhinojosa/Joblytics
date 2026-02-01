from pydantic import BaseModel, ConfigDict, Field
from typing import Annotated


class HttpPolicy(BaseModel):
    """
    HTTP execution policy for a scraping client.

    This model defines all operational parameters that control how HTTP requests
    are executed against a remote provider, including throttling, retries,
    backoff strategy, and timeouts.

    This allows different platforms (LinkedIn, Indeed, etc.) to define their own
    HTTP behavior while keeping the client implementation generic.
    """

    model_config = ConfigDict(extra="forbid")

    ## throttling
    # Maximum number of requests per second (0 = disabled)
    rate_limit_per_second: float = 0.0
    # Minimum random jitter added to throttling delay (seconds)
    jitter_seconds_min: float = 0.0
    # Maximum random jitter added to throttling delay (seconds)
    jitter_seconds_max: float = 0.0

    ## timeouts
    # TCP connection timeout (seconds)
    timeout_connect: float = 5.0
    # HTTP read timeout (seconds)
    timeout_read: float = 15.0

    ## retry/backoff
    # Maximum number of retry attempts for a single request
    max_retries: int = 3
    # Exponential backoff growth factor. Example: 2.0 → 2s, 4s, 8s, 16s...
    backoff_factor: float = 2.0
    # Maximum backoff sleep time in seconds (upper bound)
    backoff_cap: float = 30.0

    def timeout(self) -> tuple[float, float]:
        """
        Return the (connect_timeout, read_timeout) tuple.

        Returns:
            tuple[float, float]: Timeout configuration for requests.
        """
        return (self.timeout_connect, self.timeout_read)


class PolicyResolver(BaseModel):
    """
    HTTP policy resolver.

    Responsible for selecting and composing the correct HttpPolicy
    based on a provider identifier.
    """

    model_config = ConfigDict(extra="forbid")

    default: Annotated[HttpPolicy, Field(default_factory=HttpPolicy)]
    per_provider: dict[str, HttpPolicy] = Field(default_factory=dict)

    def for_provider(self, provider: str) -> HttpPolicy:
        """
        Resolve the HTTP policy for a given provider.

        The resolution logic merges:
            default policy + provider override (if exists)

        Args:
            provider (str): Logical provider identifier.

        Returns:
            HttpPolicy: Fully resolved HTTP execution policy.
        """
        override = self.per_provider.get(provider)
        if not override:
            return self.default
        return self.default.model_copy(update=override.model_dump(exclude_unset=True))
