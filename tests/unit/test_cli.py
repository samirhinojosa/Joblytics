from datetime import datetime, timezone

import pytest
from typer.testing import CliRunner

from joblytics.cli import app
from joblytics.domain.exceptions.errors import NoOffersFoundError
from joblytics.pipelines.base import PipelineReport
from joblytics.pipelines.linkedin.pipeline import LinkedInPipeline

runner = CliRunner()


@pytest.fixture(autouse=True)
def _no_op_logging(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("joblytics.cli.setup_logging", lambda *args, **kwargs: None)


def _report(produced: int = 2, sample: list[dict] | None = None) -> PipelineReport:
    now = datetime.now(timezone.utc)
    return PipelineReport(
        provider="linkedin",
        produced=produced,
        loaded=0,
        started_at=now,
        finished_at=now,
        sample_data=sample or [],
    )


def test_linkedin_command_success(monkeypatch: pytest.MonkeyPatch) -> None:
    report = _report(produced=2)
    monkeypatch.setattr(LinkedInPipeline, "run", lambda self: report)

    result = runner.invoke(app, ["linkedin", "Data Engineer", "Paris"])

    assert result.exit_code == 0
    assert "scrape started" in result.output
    assert "Finalized" in result.output


def test_linkedin_command_no_offers_found(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(self) -> PipelineReport:
        raise NoOffersFoundError(
            title="Data Engineer",
            location="Paris",
            time_posted="day",
            work_modality="onsite",
        )

    monkeypatch.setattr(LinkedInPipeline, "run", _raise)

    result = runner.invoke(app, ["linkedin", "Data Engineer", "Paris"])

    assert result.exit_code == 0
    assert "No offers results" in result.output


def test_linkedin_command_unexpected_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(self) -> PipelineReport:
        raise RuntimeError("boom")

    monkeypatch.setattr(LinkedInPipeline, "run", _raise)

    result = runner.invoke(app, ["linkedin", "Data Engineer", "Paris"])

    assert result.exit_code == 1
    assert "Error running linkedin-scrape" in result.output


def test_linkedin_command_show_table_renders_sample(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = _report(
        produced=1,
        sample=[{"title": "Data Engineer", "company": "Acme", "location": "Paris"}],
    )
    monkeypatch.setattr(LinkedInPipeline, "run", lambda self: report)

    result = runner.invoke(app, ["linkedin", "Data Engineer", "Paris", "--show-table"])

    assert result.exit_code == 0
    assert "Results preview" in result.output
    assert "Data Engineer" in result.output


def test_linkedin_command_no_show_table_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = _report(produced=1, sample=[{"title": "Data Engineer"}])
    monkeypatch.setattr(LinkedInPipeline, "run", lambda self: report)

    result = runner.invoke(app, ["linkedin", "Data Engineer", "Paris"])

    assert result.exit_code == 0
    assert "Results preview" not in result.output
