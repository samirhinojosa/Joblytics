import pytest
from pydantic import ValidationError

from joblytics.pipelines.base import TimePosted, WorkModality
from joblytics.pipelines.linkedin.models import LinkedInConfig


def _config(**overrides: object) -> LinkedInConfig:
    defaults: dict[str, object] = {"title": "Data Engineer", "location": "Paris"}
    defaults.update(overrides)
    return LinkedInConfig(**defaults)  # type: ignore[arg-type]


def test_strips_whitespace_from_title_and_location() -> None:
    config = _config(title="  Data Engineer  ", location="  Paris  ")
    assert config.title == "Data Engineer"
    assert config.location == "Paris"


def test_defaults() -> None:
    config = _config()
    assert config.distance == 10
    assert config.time_posted == TimePosted.ALL
    assert config.work_modality == WorkModality.ALL


def test_forbids_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        _config(unexpected="nope")


def test_rejects_distance_out_of_range() -> None:
    with pytest.raises(ValidationError):
        _config(distance=101)


@pytest.mark.parametrize(
    "time_posted,expected",
    [
        (TimePosted.ALL, ""),
        (TimePosted.DAY, "r86400"),
        (TimePosted.WEEK, "r604800"),
        (TimePosted.MONTH, "r2592000"),
    ],
)
def test_time_posted_value_maps_every_member(
    time_posted: TimePosted, expected: str
) -> None:
    config = _config(time_posted=time_posted)
    assert config.time_posted_value == expected


@pytest.mark.parametrize(
    "work_modality,expected",
    [
        (WorkModality.ALL, ""),
        (WorkModality.ONSITE, "1"),
        (WorkModality.HYBRID, "2"),
        (WorkModality.REMOTE, "3"),
    ],
)
def test_work_modality_value_maps_every_member(
    work_modality: WorkModality, expected: str
) -> None:
    config = _config(work_modality=work_modality)
    assert config.work_modality_value == expected
