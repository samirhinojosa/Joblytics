import random
from pathlib import Path
from typing import Self
from pydantic import BaseModel, ConfigDict, PrivateAttr, model_validator, HttpUrl
import logging
from app.core.settings import get_settings

logger = logging.getLogger(__name__)


class RandomHeaderProvider(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ua_file: str | Path | None = None

    # Internal state (not part of the scheme/validation)
    _uas: list[str] = PrivateAttr(default_factory=list)

    @model_validator(mode="after")
    def _load_from_file(self) -> Self:
        """
        Load the UAs file, filter out empty lines and comments. Save the list to _uas
        """

        ## Fetching UA file path from settings (dependencies)
        settings = get_settings()
        UA_FILE_PATH = settings.UA_FILE_PATH

        p = Path(self.ua_file).expanduser().resolve() if self.ua_file else UA_FILE_PATH

        if not p.exists():
            raise FileNotFoundError(f"UAs file not found: {p} (cwd={Path.cwd()})")

        # Reading the file
        with p.open("r", encoding="utf-8", newline="") as f:
            uas = [
                s
                for line in f
                if (s := line.strip())
                and not s.startswith("#")
                and len(s) >= 60
                and not any(
                    tok in s.lower() for tok in ("mobile", "android", "iphone", "ipad")
                )
            ]

        if not uas:
            raise ValueError("UA file is empty or only has comments/too-short lines.")

        self._uas = uas
        return self

    def user_agents(self) -> list[str]:
        """
        Return the UAs list loaded.
        """
        return list(self._uas)

    def header(self, url: HttpUrl) -> dict[str, str]:
        """
        Return a random User-Agent picked
        """
        header = {
            "User-Agent": random.choice(self._uas),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": random.choice(
                ["en-US,en;q=0.9", "fr-FR,fr;q=0.9,en;q=0.8", "es-ES,es;q=0.9,en;q=0.8"]
            ),
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1",  # Do Not Track header (simula un navegador real)
        }

        referer = None
        if "linkedin" in str(url):
            if "/jobs-guest/jobs/api/seeMoreJobPostings/" in str(url):
                referer = "https://www.linkedin.com/jobs/view/"
            elif "/jobs-guest/jobs/api/jobPosting/" in str(url):
                referer = "https://www.linkedin.com/jobs/search"

            if referer is not None:
                header["Referer"] = referer

        return header
