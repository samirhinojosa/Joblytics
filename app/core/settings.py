from enum import Enum
from pathlib import Path
from typing import Self
from functools import lru_cache
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    # Read .env and parse values
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

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
    UA_FILE_PATH: Path = (
        APP_DIR / "infrastructure" / "http" / "data" / "user_agents.txt"
    )

    # Loggin information
    LOG_LEVEL: LogLevel = LogLevel.DEBUG
    LOG_FILE: Path = Path("/var/log/joblytics/app.log")

    # Defining Logging file path
    @model_validator(mode="after")
    def override_log_file_for_debug(self) -> Self:
        """
        - If DEBUG -> use local log: logs/joblytics.log
        - If not DEBUT -> default /var/log/joblytics/app.log
        """
        if self.LOG_LEVEL == LogLevel.INFO:
            self.LOG_FILE = Path("logs/joblytics.log")
        return self

    def resolve_log_file(self) -> Path:
        p = self.LOG_FILE
        return p if p.is_absolute() else (self.PROJECT_ROOT / p).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
