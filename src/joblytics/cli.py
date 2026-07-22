import typer
import logging
from joblytics.core.config.settings import get_settings
from joblytics.core.config.logger import setup_logging
from joblytics.core.utils.cli import render_table
from joblytics.pipelines.base import TimePosted, WorkModality
from joblytics.domain.exceptions.errors import NoOffersFoundError
from joblytics.domain.repositories.raw_job_offer_repository import (
    RawJobOfferRepository,
)
from joblytics.infrastructure.repositories.snowflake_raw_job_offer_repository import (
    SnowflakeRawJobOfferRepository,
)
from joblytics.pipelines.linkedin.pipeline import LinkedInPipeline


logger = logging.getLogger("joblytics")

app = typer.Typer()


@app.callback()
def main(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable logs in DEBUG level.",
    ),
) -> None:
    """
    CLI of project utilities.
    """
    settings = get_settings()
    setup_logging(settings, verbose=verbose)

    logging.getLogger("joblytics").debug("CLI initialized (verbose=%s)", verbose)


@app.command("linkedin")
def linkedIn_scrapper(
    title: str,
    location: str,
    time_posted: TimePosted = typer.Argument(
        TimePosted.DAY,
        help="LinkedIn publication date: all, day (24h), week (7d), month (30d).",
    ),
    work_modality: WorkModality = typer.Argument(
        WorkModality.ALL,
        help="LinkedIn work modality: all, onsite, hybrid, remote.",
    ),
    show_table: bool = typer.Option(
        False,
        "--show-table/--no-show-table",
        help="Enable or disable console table rendering.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Scrape without writing results to Snowflake.",
    ),
) -> None:
    """
    Extracts job postings from LinkedIn and displays a summary table in the console.
    """

    try:
        color = typer.colors.GREEN
        typer.secho(
            f"✨ [LinkedIn] scrape started (title={title}, "
            f"location={location}, time_posted={time_posted.value}, "
            f"work_modality={work_modality.value}, dry_run={dry_run}).",
            fg=color,
        )

        repository: RawJobOfferRepository | None = None
        if dry_run:
            typer.secho(
                "🧪 Dry-run mode: results will not be written to Snowflake.",
                fg=typer.colors.YELLOW,
            )
        else:
            repository = SnowflakeRawJobOfferRepository(get_settings())

        pipeline = LinkedInPipeline(
            provider="linkedin",
            title=title,
            location=location,
            time_posted=time_posted,
            work_modality=work_modality,
            repository=repository,
        )

        report = pipeline.run()

        if show_table and report.sample_data:
            typer.echo("### 📋 Results preview (Top 5) ###")

            table = render_table(
                report.sample_data,
                drop={
                    "provider",
                    "provider_job_id",
                    "url",
                    "description",
                    "scraped_at",
                    "raw_description_html",
                    "search_title",
                    "search_location",
                    "search_work_modality",
                    "search_time_posted",
                    "raw",
                },
                col_limits={
                    "title": 45,
                    "company": 30,
                    "location": 25,
                },
            )

            typer.echo("-" * 100)
            print(table)
            typer.echo("-" * 100)

        color = typer.colors.GREEN if report.produced > 0 else typer.colors.YELLOW
        typer.secho("🟢 [LinkedIn] Finalized.", fg=color)

    except NoOffersFoundError as e:
        logger.warning(f"No results found: {e}")
        typer.secho(f"🟡 No offers results. Info: {e}.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=0)
    except Exception as e:
        logger.exception("Error running linkedin-scrape")
        typer.secho(
            f"🔴 Error running linkedin-scrape: {e}", err=True, fg=typer.colors.RED
        )
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
