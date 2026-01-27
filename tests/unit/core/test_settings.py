import pytest
from pathlib import Path
from joblytics.core.config.settings import Settings, get_settings, LogLevel
from joblytics.core.config.logger import compute_log_file


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


def test_compute_log_file_verbose(tmp_path: Path):
    settings = get_settings(
        read_env=False, PROJECT_ROOT=tmp_path, LOG_LEVEL=LogLevel.INFO
    )
    p = compute_log_file(settings, verbose=True)
    assert str(p).startswith(str(tmp_path))
    assert str(p).endswith("logs/joblytics.log")
