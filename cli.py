import typer
import pandas as pd
from app.core.settings import get_settings
from app.core.logging_config import setup_logging
from app.infrastructure.ingestion.linkedin_scrapper import LinkedInScrapper, TimePosted

app = typer.Typer()

settings = get_settings(LOG_LEVEL="INFO")
setup_logging(settings)

pd.set_option("display.max_colwidth", 30)  # Maximum 100 characters per cell
pd.set_option("display.width", 100)  # Maximum total table width
pd.set_option("display.max_columns", None)  # Show all columns
pd.set_option("display.expand_frame_repr", False)  # Do not split across multiple lines


@app.command()
def linkedIn_scrapper(
    title: str,
    location: str,
    time_posted: TimePosted = typer.Option(
        TimePosted.DAY,
        help="LinkedIn publication date: all, day (24h), week (7d), month (30d).",
    ),
):
    scrapper = LinkedInScrapper(title=title, location=location, time_posted=time_posted)
    jobs_summary = scrapper.fetch_offers_summary()
    jobs_details = scrapper.fetch_offers_details(jobs_summary)

    df = pd.DataFrame(jobs_details)
    df = df.drop(columns=["url", "description"]).to_markdown(index=False)
    print(df)


if __name__ == "__main__":
    app()
