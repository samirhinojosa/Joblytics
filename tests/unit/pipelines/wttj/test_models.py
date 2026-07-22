import pytest
from pydantic import ValidationError

from joblytics.pipelines.base import TimePosted, WorkModality
from joblytics.pipelines.wttj.models import WTTJConfig


def _config(**overrides: object) -> WTTJConfig:
    defaults: dict[str, object] = {"title": "Data Engineer", "location": "Paris"}
    defaults.update(overrides)
    return WTTJConfig(**defaults)  # type: ignore[arg-type]


def test_strips_whitespace_from_title_and_location() -> None:
    config = _config(title="  Data Engineer  ", location="  Paris  ")
    assert config.title == "Data Engineer"
    assert config.location == "Paris"


def test_defaults() -> None:
    config = _config()
    assert config.time_posted == TimePosted.ALL
    assert config.work_modality == WorkModality.ALL


def test_forbids_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        _config(unexpected="nope")


def test_rejects_blank_title() -> None:
    with pytest.raises(ValidationError):
        _config(title="")
