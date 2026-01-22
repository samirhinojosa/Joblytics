from joblytics.core.config.settings import Settings
from logging.config import dictConfig
from pathlib import Path


def compute_log_file(settings: Settings, verbose: bool) -> Path:
    return (
        (settings.PROJECT_ROOT / "logs/joblytics.log")
        if verbose
        else settings.resolve_log_file()
    )


def setup_logging(settings: Settings, verbose: bool = False) -> None:
    """
    Logging policy:
      - App logs (joblytics.*): INFO by default, DEBUG with --verbose.
      - Third-party logs: WARNING by default.
    """

    app_level = "DEBUG" if verbose else "INFO"
    THIRD_PARTY_LEVEL = "WARNING"

    # Defining Logging file path
    # log_file: Path = (
    #     Path("logs/joblytics.log") if verbose else settings.resolve_log_file()
    # )
    log_file = compute_log_file(settings, verbose)

    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("a"):
            pass
    except Exception:
        fallback = settings.PROJECT_ROOT / settings.LOG_FILE
        fallback.parent.mkdir(parents=True, exist_ok=True)
        log_file = fallback

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            # Colors on console
            "colored": {
                "()": "colorlog.ColoredFormatter",
                "format": "%(log_color)s[%(asctime)s] [%(levelname)s] (%(module)s): %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "log_colors": {
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red",
                },
            },
            "standard": {
                "format": "[%(asctime)s] [%(levelname)s] %(module)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            # Technical console (for debugging and errors)
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "colored",
                "level": "DEBUG",  # keep handlers open; control via logger levels
            },
            # File for technical logs
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(log_file),
                "formatter": "standard",
                "level": "DEBUG",
                "maxBytes": 10 * 1024 * 1024,  # 10 MB
                "backupCount": 7,
                "encoding": "utf-8",
                "delay": True,
            },
        },
        # Root is quiet
        "root": {
            "handlers": ["console", "file"],
            "level": THIRD_PARTY_LEVEL,
        },
        # Only app namespace is chatty
        "loggers": {
            "joblytics": {
                "handlers": ["console", "file"],
                "level": app_level,
                "propagate": False,
            },
            # Optional: pin typical noisy libs to third_party_level
            "urllib3": {"level": THIRD_PARTY_LEVEL},
            "requests": {"level": THIRD_PARTY_LEVEL},
            "httpx": {"level": THIRD_PARTY_LEVEL},
        },
    }

    dictConfig(logging_config)
