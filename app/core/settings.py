from enum import Enum
from pathlib import Path
from typing import Self, Any
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
    DESCRIPTION: str = (
        "Joblytics is a Python-based tool to scrape and analyze job listings "
        "from platforms such as LinkedIn, Welcome to the Jungle, among others.<br/>"
        "It is designed with Clean Architecture principles and built using technologies "
        "such as: DBT, Docker, FastAPI, ensuring maintainability, scalability, and modularity."
    )
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
    LOG_LEVEL: LogLevel = LogLevel.INFO
    LOG_FILE: Path = Path("/var/log/joblytics/app.log")

    # Defining Logging file path
    @model_validator(mode="after")
    def override_log_file_for_debug(self) -> Self:
        """
        - If DEBUG -> use local log: logs/joblytics.log
        - If not DEBUT -> default /var/log/joblytics/app.log
        """
        if self.LOG_LEVEL == LogLevel.DEBUG:
            self.LOG_FILE = Path("logs/joblytics.log")
        return self

    def resolve_log_file(self) -> Path:
        p = self.LOG_FILE
        return p if p.is_absolute() else (self.PROJECT_ROOT / p).resolve()


class RuntimeSettings(Settings):
    # Reads .env (runtime/default)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


class TestSettings(Settings):
    # Ignores .env (unit tests)
    model_config = SettingsConfigDict(
        env_file=None,
        case_sensitive=False,
    )


@lru_cache
def get_settings(*, read_env: bool = True, **overrides: Any) -> Settings:
    """
    Runtime: get_settings()               -> reads .env (cached).
    Tests:   get_settings(read_env=False) -> ignores .env; pass overrides explicitly.
    """
    cls = RuntimeSettings if read_env else TestSettings
    return cls(**overrides)
