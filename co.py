from app.infrastructure.http.header_provider import RandomHeaderProvider
from app.infrastructure.ingestion.linkedin_scrapper import LinkedinScrapper, TimePosted
from app.infrastructure.http.scrape_client import ScrapeClient


linkedin_scrapper = LinkedinScrapper(
    title="Data Engineer",
    location="Paris",
    time_posted=TimePosted.WEEK
)
# url = linkedin_scrapper.generate_url()

# print(url)
# http = ScrapeClient(web_page_search=url)
# response = http.fetch_job_search()
# print(response.text)
# print(linkedin_scrapper.number_of_offers(response))c






print(linkedin_scrapper.fetching_offers())
