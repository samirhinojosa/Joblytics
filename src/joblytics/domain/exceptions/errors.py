from pydantic import HttpUrl


class DomainError(Exception):
    """Basis for domain errors (non-technical)."""


class NoOffersFoundError(DomainError):
    def __init__(
        self,
        title: str,
        location: str,
        # distance: int,
        time_posted: str,
        work_modality: str,
        url: HttpUrl | None = None,
    ):
        self.title = title
        self.location = location
        # self.distance = distance
        self.time_posted = time_posted
        self.work_modality = work_modality
        self.url = url

        super().__init__(
            f"No offers were found (0 results) for "
            f'title="{title}", location="{location}", distance={distance}, '
            f"time posted={time_posted}, remote mode={work_modality}"
            + (f". URL: {url}" if url else "")
        )
