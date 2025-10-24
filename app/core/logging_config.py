import logging
from logging.config import dictConfig
from pathlib import Path
from app.core.settings import get_settings


def setup_logging() -> None:

    settings = get_settings()

    LOG_LEVEL = settings.LOG_LEVEL.upper()
    LOG_FILE = Path(settings.LOG_FILE)

    if LOG_FILE.parent and not LOG_FILE.parent.exists():
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)   
 
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,

        "formatters": {
            "standard": {
                "format": "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
            },
            "user": {
                "format": "%(message)s"
            },
        },

        "handlers": {
            # Technical console (for debugging and errors)
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": LOG_LEVEL
            },
            # Messages visible to the user
            "user_console": {
                "class": "logging.StreamHandler",
                "formatter": "user",
                "level": "INFO"
            },
            # File for technical logs
            "file": {
                "class": "logging.FileHandler",
                "filename": LOG_FILE,
                "formatter": "standard",
                "level": "WARNING"
            },
        },

        "loggers": {
            # Main logger
            "app": {
                "handlers": ["console", "file"],
                "level": LOG_LEVEL,
                "propagate": False
            },
            # Separate logger for user messages
            "user": {
                "handlers": ["user_console"],
                "level": "INFO",
                "propagate": False
            },
        }
    }

    dictConfig(LOGGING_CONFIG)