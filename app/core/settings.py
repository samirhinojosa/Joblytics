import os
from pathlib import Path
from dotenv import load_dotenv
from functools import lru_cache
from pydantic_settings import BaseSettings

# load .env
load_dotenv(override=True)

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

    # General API information
    # OPENAPI_URL: str = "/openapi.json"

    # ## current API version
    # API_VERSION: str = "/api/v1"
    # FAST_API_VERSION: str = "0.0.1"

    ## User agents file
    UA_FILE_PATH: Path = APP_DIR / "infrastructure" / "http" / "data" / "user_agents.txt"

    class Config:
        env_file = ".env"    

@lru_cache
def get_settings():
    return Settings()      