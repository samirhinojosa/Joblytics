from pydantic import BaseModel, ConfigDict
from typing import Iterable, ClassVar
from pathlib import Path
from app.core.settings import get_settings

settings = get_settings()

class RandomHeaderProvider(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    user_agents: Iterable[str] | None = None
    ua_file: str | None = None

    DEFAULT_UA_PATH: ClassVar[Path] = Path(settings.UA_FILE)


    if not DEFAULT_UA_PATH.exists():
        raise FileNotFoundError(f"UAs file not found: {DEFAULT_UA_PATH}")
    else:
        print(f"file exists: {DEFAULT_UA_PATH}")


