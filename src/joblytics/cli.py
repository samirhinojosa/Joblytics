import typer

from joblytics.core.config.settings import get_settings
from joblytics.core.config.logger import setup_logging
from joblytics.pipelines.linkedin_scrapper import (
    LinkedInScrapper,
    TimePosted,
    WorkModality,
)
from joblytics.domain.exceptions.errors import NoOffersFoundError
from joblytics.core.utils.cli import render_table

app = typer.Typer()


@app.callback()
def main(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Activa logs en nivel DEBUG.",
    ),
) -> None:
    """
    CLI of project utilities.
    """
    settings = get_settings()
    setup_logging(settings, verbose=verbose)

    import logging

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
) -> None:
    """
    Extracts job postings from LinkedIn and displays a summary table in the console.
    """
    import logging

    logger = logging.getLogger("joblytics")

    try:
        logger.info(
            f"LinkedIn scrape started (title={title}, location={location}, time_posted={time_posted.value}, work_modality={work_modality.value})"
        )

        scrapper = LinkedInScrapper(
            title=title,
            location=location,
            time_posted=time_posted,
            work_modality=work_modality,
        )
        jobs_summary = scrapper.fetch_offers_summary() or []
        logger.debug(f"Fetched summary offers: {len(jobs_summary)}")

        jobs_details = scrapper.fetch_offers_details(jobs_summary)
        if not jobs_details:
            logger.warning("No job details fetched.")
            return
        logger.debug(f"Fetched job details: {len(jobs_details)}")

        if show_table:
            logger.info("Rendering summary table in console output")

            table = render_table(
                jobs_details[:10],
                drop={"id", "url", "description"},
                col_limits={
                    "title": 45,
                    "company": 30,
                    "location": 25,
                    "contract_type": 15,
                    "salary": 18,
                },
            )

            print(table)

        logger.info("LinkedIn scrape finished successfully")
    except NoOffersFoundError as e:
        logger.warning(str(e))
        typer.echo("No offers found. Exiting.")
        raise typer.Exit(code=0)
    except Exception as e:
        logger.exception("Error running linkedin-scrape")
        typer.secho(
            f"Error running linkedin-scrape: {e}", err=True, fg=typer.colors.RED
        )
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
