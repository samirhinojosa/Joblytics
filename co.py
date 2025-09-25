from app.infrastructure.http.header_provider import RandomHeaderProvider
from app.infrastructure.ingestion.linkedin_scrapper import LinkedinScrapper
from app.infrastructure.http.scrape_client import ScrapeClient


linkedin_scrapper = LinkedinScrapper(
    title="Data Engineer",
    location="Grenoble"
)
url = linkedin_scrapper.generate_url()


http = ScrapeClient(job_search_url=url)
response = http.fetch_job_search()
print(response.text)

