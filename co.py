import logging
from app.infrastructure.http.header_provider import RandomHeaderProvider
from app.infrastructure.ingestion.linkedin_scrapper import LinkedinScrapper, TimePosted
from app.infrastructure.http.scraper.scrape_client import ScrapeClient
from app.core.logging_config import setup_logging
from app.core.settings import get_settings


def main():
    setup_logging()
    settings = get_settings()

    # log = logging.getLogger("app")

    linkedin_scrapper = LinkedinScrapper(
        title="Data engineer",
        location="France",
        time_posted=TimePosted.MONTH
    )

    print(linkedin_scrapper.fetching_offers())

    # import time

    # counter = 20
    # print(counter % 10)
    # if (counter % 5) == 0:
    #     time.sleep(0.5)


if __name__ == "__main__":
    main()
    
    # url = linkedin_scrapper.generate_url()

    # print(url)
    # http = ScrapeClient(web_page_search=url)
    # response = http.fetch_job_search()
    # print(response.text)
    # print(linkedin_scrapper.number_of_offers(response))c






