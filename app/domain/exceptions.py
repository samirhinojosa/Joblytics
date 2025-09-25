
# Dominio: excepciones específicas
class DomainError(Exception):
    """Base para errores de dominio (no técnicos)."""


class NoOffersFoundError(DomainError):

    def __init__(
        self, *,
        title: str,
        location: str,
        distance: int,
        time_posted: str,
        remote_mode: str,
        url: str | None = None
    ):
        
        self.title = title
        self.location = location
        self.distance = distance
        self.time_posted = time_posted
        self.remote_mode = remote_mode
        self.url = url

        msg = (
            f"No offers were found (0 resultados) for"
            f'title="{title}", location="{location}", distance={distance}, '
            f"time posted={time_posted}, remote mode={remote_mode}"
            + (f". URL: {url}" if url else "")
        )
        
        super().__init__(msg)