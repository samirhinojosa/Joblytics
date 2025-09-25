from app.infrastructure.http.header_provider import RandomHeaderProvider
from app.infrastructure.ingestion.linkedin_scrapper import LinkedinScrapper, TimePosted
from app.infrastructure.http.scrape_client import ScrapeClient


linkedin_scrapper = LinkedinScrapper(
    title="Data Engineer",
    location="Paris",
    time_posted=TimePosted.WEEK
)
url = linkedin_scrapper.generate_url()


http = ScrapeClient(job_search_url=url)
response = http.fetch_job_search()
print(response.text)
print(linkedin_scrapper.number_of_offers(response))

# linkedin_scrapper._number_of_offers = 30

# print(linkedin_scrapper._number_of_offers)


print(linkedin_scrapper.fetching_offers(response))
