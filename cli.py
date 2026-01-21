import typer
import pandas as pd
from app.core.settings import get_settings
from app.core.logging_config import setup_logging
from app.infrastructure.ingestion.linkedin_scrapper import LinkedInScrapper, TimePosted

app = typer.Typer()


@app.callback()
def main(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Activa logs en nivel DEBUG.",
    ),
):
    """
    CLI of project utilities.
    """
    settings = get_settings(LOG_LEVEL="DEBUG" if verbose else "INFO")
    setup_logging(settings)

    # Pandas configuration (for console output only)
    pd.set_option("display.max_colwidth", 30)  # Maximum 100 characters per cell
    pd.set_option("display.width", 100)  # Maximum total table width
    pd.set_option("display.max_columns", None)  # Show all columns
    pd.set_option("display.expand_frame_repr", False)  # Not split across multiple lines


@app.command("linkedin-scrape")
def linkedIn_scrapper(
    title: str,
    location: str,
    time_posted: TimePosted = typer.Option(
        TimePosted.DAY,
        help="LinkedIn publication date: all, day (24h), week (7d), month (30d).",
    ),
):
    """
    Extracts job postings from LinkedIn and displays a summary table in the console.
    """
    try:
        scrapper = LinkedInScrapper(
            title=title, location=location, time_posted=time_posted
        )
        jobs_summary = scrapper.fetch_offers_summary()
        jobs_details = scrapper.fetch_offers_details(jobs_summary)

        df = pd.DataFrame(jobs_details)
        df = df.drop(columns=["url", "description"]).to_markdown(index=False)
        print(df)
    except Exception as e:
        typer.secho(
            f"Error running linkedin-scrape: {e}", err=True, fg=typer.colors.RED
        )
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
