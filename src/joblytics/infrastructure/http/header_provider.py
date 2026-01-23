import random
from pathlib import Path
from typing import Self
from pydantic import BaseModel, ConfigDict, PrivateAttr, model_validator, HttpUrl, Field
import logging
from joblytics.core.config.settings import Settings, get_settings

logger = logging.getLogger("joblytics")


class RandomHeaderProvider(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ua_file: str | Path | None = None

    # Internal state (not part of the scheme/validation)
    _uas: list[str] = PrivateAttr(default_factory=list)

    settings: Settings = Field(default_factory=get_settings)

    @model_validator(mode="after")
    def _load_from_file(self) -> Self:
        """
        Load the UAs file, filter out empty lines and comments. Save the list to _uas
        """

        if self.ua_file:
            p = Path(self.ua_file).expanduser().resolve()
        else:
            ## Fetching UA file path from settings (dependencies)
            p = self.settings.resolve_ua_file_path().expanduser().resolve()

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
        headers, _ua = self.header_bundle(url)
        return headers

    def header_bundle(self, url: HttpUrl) -> tuple[dict[str, str], str]:
        """
        Return (headers, user_agent) so callers can enforce robots.txt with the same UA.
        """
        user_agent = random.choice(self._uas)
        header = {
            "User-Agent": user_agent,
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

        return header, user_agent
