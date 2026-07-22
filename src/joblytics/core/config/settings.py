from enum import Enum
from pathlib import Path
from typing import Any
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from joblytics.core.config.policy import HttpPolicy, PolicyResolver


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
    CONTACT: dict[str, str] = {
        "name": "Samir Hinojosa",
        "url": "https://github.com/samirhinojosa",
        "email": "samirhinojosa@gmail.com",
    }
    LICENSE_INFO: dict[str, str] = {
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    }

    # Paths
    PACKAGE_ROOT: Path = Path(__file__).resolve().parents[2]  # src/joblytics
    SRC_ROOT: Path = Path(__file__).resolve().parents[3]  # src
    PROJECT_ROOT: Path = Path(__file__).resolve().parents[4]  # repo root

    # timezone
    TZ: str = "UTC"

    # Database information (real credentials read from .env)
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "pwd"
    POSTGRES_DB: str = "db"

# Snowflake Credentials (real credentials read from .env)
    SNOWFLAKE_ACCOUNT: str = ""
    SNOWFLAKE_USER: str = ""
    SNOWFLAKE_PASSWORD: str = ""
    SNOWFLAKE_ROLE: str = "ACCOUNTADMIN"
    SNOWFLAKE_WAREHOUSE: str = "DEMO_WH"

    # --- Snowflake Infrastructure: Bronze Layer (Raw Ingestion for Python Scraper) ---
    SNOWFLAKE_RAW_DATABASE: str = "RAW_DB"
    SNOWFLAKE_RAW_SCHEMA: str = "LINKEDIN"
    SNOWFLAKE_STAGE: str = "JOBLYTICS_RAW_STAGE"
    SNOWFLAKE_TABLE: str = "RAW_LINKEDIN_JOBS"

    # --- Snowflake Infrastructure: Target Analytics (dbt Transformation Layer) ---
    SNOWFLAKE_ANALYTICS_DATABASE: str = "ANALYTICS_DB"

    ## User agents file (optional override; infrastructure resolves its own default)
    UA_FILE_PATH: Path | None = None

    # Loggin information
    LOG_LEVEL: LogLevel = LogLevel.INFO
    LOG_FILE: Path = Path("/var/log/joblytics/app.log")

    # HTTP POLICIES : reliability / Scraping settings / Compliance
    HTTP_POLICIES: PolicyResolver = PolicyResolver(
        default=HttpPolicy(
            rate_limit_per_second=0.0,
            jitter_seconds_min=0.0,
            jitter_seconds_max=0.0,
            timeout_connect=5.0,
            timeout_read=15.0,
            max_retries=3,
            backoff_factor=2.0,
            backoff_cap=30.0,
        ),
        per_provider={
            "linkedin": HttpPolicy(
                rate_limit_per_second=0.5,
                jitter_seconds_min=1.5,
                jitter_seconds_max=3.5,
                timeout_connect=5.0,
                timeout_read=15.0,
                max_retries=3,
                backoff_factor=2.0,
                backoff_cap=30.0,
            ),
            "indeed": HttpPolicy(
                rate_limit_per_second=0.5,
                jitter_seconds_min=0.05,
                jitter_seconds_max=0.25,
                timeout_connect=3.0,
                timeout_read=10.0,
                max_retries=2,
                backoff_factor=1.5,
                backoff_cap=20.0,
            ),
        },
    )

    def resolve_log_file(self) -> Path:
        p = self.LOG_FILE
        return p if p.is_absolute() else (self.PROJECT_ROOT / p).resolve()

    def http_policy(self, provider: str) -> HttpPolicy:
        return self.HTTP_POLICIES.for_provider(provider)


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
