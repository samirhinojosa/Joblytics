# import logging
from logging.config import dictConfig
from pathlib import Path
from colorlog import ColoredFormatter
from app.core.settings import get_settings


def setup_logging() -> None:

    settings = get_settings()

    LOG_LEVEL = settings.LOG_LEVEL.upper()
    LOG_FILE : Path = settings.resolve_log_file()

    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a"):
            pass
    except Exception:
        fallback = settings.PROJECT_ROOT / settings.LOG_FILE
        fallback.parent.mkdir(parents=True, exist_ok=True)
        LOG_FILE = fallback
 
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,

        "formatters": {
            # Colors on console
            "colored": {
                "()": "colorlog.ColoredFormatter",
                "format": "%(log_color)s[%(asctime)s] [%(levelname)s] (%(name)s): %(message)s",
                "log_colors": {
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red",
                },
            },
            "standard": {
                "format": "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
            },
        },

        "handlers": {
            # Technical console (for debugging and errors)
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "colored",
                "level": LOG_LEVEL
            },
            # File for technical logs
            "file": {
                "class": "logging.FileHandler",
                "filename": str(LOG_FILE),
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
        }
    }

    dictConfig(LOGGING_CONFIG)