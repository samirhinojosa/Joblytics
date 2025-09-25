import random
from pathlib import Path
from pydantic import BaseModel, ConfigDict, PrivateAttr, model_validator
from app.core.settings import get_settings
# from core.settings import get_settings


class RandomHeaderProvider(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    ua_file: str | Path | None = None

    # Internal state (not part of the scheme/validation)
    _uas: list[str] = PrivateAttr(default_factory=list)    
    
    @model_validator(mode="after")
    def _load_from_file(self):
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
            uas = [s for line in f 
                   if (s := line.strip()) 
                   and not s.startswith("#") 
                   and len(s) >= 60
                   and not any(tok in s.lower() for tok in ("mobile", "android", "iphone", "ipad"))]

        if not uas:
            raise ValueError("UA file is empty or only has comments/too-short lines.")

        self._uas = uas
        return self
    
    def user_agents(self) -> list[str]:
        """
        Return the UAs list loaded.
        """
        return list(self._uas)
    
    def header(self) -> dict[str, str]:
        """
        Return a random User-Agent picked
        """
        return {"User-Agent": random.choice(self._uas)}