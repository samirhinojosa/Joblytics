import typer
from tabulate import tabulate
from typing import Any, Mapping, Sequence
from joblytics.core.config.settings import get_settings
from joblytics.core.config.logger import setup_logging
from joblytics.infrastructure.ingestion.linkedin_scrapper import (
    LinkedInScrapper,
    TimePosted,
)

app = typer.Typer()


def render_table(rows: Sequence[Mapping[str, Any]], *, drop: set[str]) -> Any:
    """
    Render table in CLI
    """
    if not rows:
        return "No results."

    cols = [k for k in rows[0].keys() if k not in drop]
    table = [[r.get(c, "") for c in cols] for r in rows]

    return tabulate(
        table,
        headers=cols,
        tablefmt="github",
        showindex=False,
    )


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

    logging.getLogger(__name__).debug("CLI initialized (verbose=%s)", verbose)


@app.command("linkedin-scrape")
def linkedIn_scrapper(
    title: str,
    location: str,
    time_posted: TimePosted = typer.Option(
        TimePosted.DAY,
        help="LinkedIn publication date: all, day (24h), week (7d), month (30d).",
    ),
) -> None:
    """
    Extracts job postings from LinkedIn and displays a summary table in the console.
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.info(
            f"LinkedIn scrape started (title={title}, location={location}, time_posted={time_posted.value})"
        )

        scrapper = LinkedInScrapper(
            title=title, location=location, time_posted=time_posted
        )
        jobs_summary = scrapper.fetch_offers_summary() or []
        logger.debug(f"Fetched summary offers: {len(jobs_summary)}")

        jobs_details = scrapper.fetch_offers_details(jobs_summary)
        if not jobs_details:
            logger.warning("No job details fetched.")
            return
        logger.debug(f"Fetched job details: {len(jobs_details)}")

        table = render_table(jobs_details, drop={"url", "description"})

        # df = pd.DataFrame(jobs_details)
        # df = df.drop(columns=["url", "description"]).to_markdown(index=False)
        print(table)

        logger.info("LinkedIn scrape finished successfully")
    except Exception as e:
        logger.exception("Error running linkedin-scrape")
        typer.secho(
            f"Error running linkedin-scrape: {e}", err=True, fg=typer.colors.RED
        )
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
