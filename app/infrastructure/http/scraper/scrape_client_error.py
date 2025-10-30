from pydantic import HttpUrl

class ScrapeClientError(RuntimeError):

    def __init__(
        self, 
        url: HttpUrl,
        max_retries: int | None = None,
        attempts: int | None = None,
        status: int | None = None
    ):
        
        self.url = url
        self.max_retries = max_retries
        self.attempts = attempts
        self.status = status

        message = f"Failed to GET: {url} (attempt {self.attempts}/{self.max_retries}) " + \
                    f"last status={status}"

        super().__init__(message)