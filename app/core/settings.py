# import os
from pathlib import Path
# from dotenv import load_dotenv
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

# load .env
# load_dotenv(override=True)

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
    LOG_LEVEL: str = "DEBUG"                # Logger level (“DEBUG,” “INFO,” “WARNING,” “ERROR”)
    LOG_FILE: str = "logs/joblytics.log"    # File where logs are stored (dev mode)

    # class Config:
    #     env_file = ".env"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    def resolve_log_file(self) -> Path:
        p = Path(self.LOG_FILE)
        if p.is_absolute():
            return p
        # Interpret relative to the project root
        return (self.PROJECT_ROOT / p).resolve()

@lru_cache
def get_settings() -> Settings:
    return Settings()      