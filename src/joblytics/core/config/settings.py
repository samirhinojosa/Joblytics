from enum import Enum
from pathlib import Path
from typing import Any
from functools import lru_cache
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

    # timezone
    TZ: str = "UTC"

    # Database information (real credentials read from .env)
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "pwd"
    POSTGRES_DB: str = "db"

    # General API information
    # OPENAPI_URL: str = "/openapi.json"

    # ## current API version
    # API_VERSION: str = "/api/v1"
    # FAST_API_VERSION: str = "0.0.1"

    ## User agents file
    # UA_FILE_PATH: Path = Path(
    #     "src/joblytics/infrastructure/http/assets/user_agents.txt"
    # )
    UA_FILE_PATH: Path = (
        PROJECT_ROOT / "infrastructure" / "http" / "assets" / "user_agents.txt"
    )

    # Loggin information
    LOG_LEVEL: LogLevel = LogLevel.INFO
    LOG_FILE: Path = Path("/var/log/joblytics/app.log")

    # Compliance / responsible scraping (B3)
    RATE_LIMIT_PER_SECOND: float = 0.2  # 1 req every 5 seconds
    JITTER_SECONDS_MIN: float = 0.1
    JITTER_SECONDS_MAX: float = 0.4

    RESPECT_ROBOTS: bool = False
    DRY_RUN: bool = False

    # HTTP / reliability
    REQUEST_TIMEOUT_CONNECT: float = 5.0
    REQUEST_TIMEOUT_READ: float = 15.0
    MAX_RETRIES: int = 3
    BACKOFF_FACTOR: float = 2.0
    BACKOFF_CAP: float = 30.0

    def resolve_ua_file_path(self) -> Path:
        p = self.UA_FILE_PATH
        return p if p.is_absolute() else (self.PROJECT_ROOT / p).resolve()

    def resolve_log_file(self) -> Path:
        p = self.LOG_FILE
        return p if p.is_absolute() else (self.PROJECT_ROOT / p).resolve()

    def resolve_timeout(self) -> tuple[float, float]:
        return (self.REQUEST_TIMEOUT_CONNECT, self.REQUEST_TIMEOUT_READ)


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
    cls = TestSettings if not read_env else RuntimeSettings
    return cls(**overrides)
