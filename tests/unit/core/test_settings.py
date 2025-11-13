import pytest
from pathlib import Path
from app.core.settings import Settings, get_settings, LogLevel


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    settings = get_settings(
        read_env=False, PROJECT_ROOT=tmp_path, LOG_LEVEL=LogLevel.INFO
    )
    return settings


def test_resolve_log_file(tmp_path: Path) -> None:
    settings = get_settings(
        read_env=False, PROJECT_ROOT=tmp_path, LOG_LEVEL=LogLevel.INFO
    )
    settings.LOG_FILE = Path("logs/joblytics.log")
    resolved = settings.resolve_log_file()
    assert resolved.is_absolute()
    assert str(resolved).startswith(str(tmp_path))


def test_override_log_file_for_debug(tmp_path: Path) -> None:
    settings = get_settings(
        read_env=False, PROJECT_ROOT=tmp_path, LOG_LEVEL=LogLevel.DEBUG
    )
    p = settings.resolve_log_file()
    assert "logs/joblytics.log" in str(p)
