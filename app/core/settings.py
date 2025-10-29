# import os
from enum import Enum
from pathlib import Path
from typing import Optional
# from dotenv import load_dotenv
from functools import lru_cache
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# load .env
# load_dotenv(override=True)

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class Settings(BaseSettings):

    # General information
    APP_NAME: str = "Joblytics"
    # DESCRIPTION: str = """Twitter (now X) Monitor AI is an intelligent service that monitors and analyzes tweets in real time.<br/>
    # It is designed with Clean Architecture principles and built using FastAPI and Docker, ensuring maintainability, scalability, and modularity."""
    CONTACT: dict = {
        "name": "Samir Hinojosa",
        "url": "https://github.com/samirhinojosa",
        "email": "samirhinojosa@gmail.com",
    }
    LICENSE_INFO: dict = {
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    }
    APP_DIR: Path = Path(__file__).resolve().parent.parent
    PROJECT_ROOT: Path = APP_DIR.parent

    # General API information
    # OPENAPI_URL: str = "/openapi.json"

    # ## current API version
    # API_VERSION: str = "/api/v1"
    # FAST_API_VERSION: str = "0.0.1"

    ## User agents file
    UA_FILE_PATH: Path = APP_DIR / "infrastructure" / "http" / "data" / "user_agents.txt"

    # Loggin information
    LOG_LEVEL: LogLevel = LogLevel.DEBUG
    LOG_FILE: Optional[Path] = None

    # Variables present in .env: LOG_FILE
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Defining Logging file path
    @model_validator(mode="after")
    def override_log_file_for_debug(self):
        """
        - If DEBUG -> use local log: logs/joblytics.log
        - If not DEBUT and LOG_FILE is None -> log path: /var/log/joblytics/app.log
        """
        if self.LOG_LEVEL == LogLevel.DEBUG:
            self.LOG_FILE = Path("logs/joblytics.log")
        elif self.LOG_FILE is None:
            self.LOG_FILE = Path("/var/log/joblytics/app.log")
        return self    

    def resolve_log_file(self) -> Path:
        lf = self.LOG_FILE
        assert lf is not None, "LOG_FILE should be resolved in the validator 'override_log_file_for_debug'"
        p = lf if isinstance(lf, Path) else Path(lf)
        return p if p.is_absolute() else (self.PROJECT_ROOT / p).resolve()

@lru_cache
def get_settings() -> Settings:
    return Settings()      