PAGE_SIZE: int = 10

# Base URLs for LinkedIn
LINKEDIN_SEARCH_URL = "https://www.linkedin.com/jobs/search"
LINKEDIN_API_SEARCH_URL = (
    "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
)
LINKEDIN_DETAILS_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/"


# Mapping dictionaries (Translation from our app -> LinkedIn)
TIME_POSTED_MAP = {
    "all": "",
    "day": "r86400",
    "week": "r604800",
    "month": "r2592000",
}

WORK_MODALITY_TO_LINKEDIN = {
    "all": "",
    "onsite": "1",
    "hybrid": "2",
    "remote": "3",
}


# CSS search selectors (summary)
SUMMARY_SELECTORS = {
    "job_count": "span.results-context-header__job-count",
    "geo_id_input": 'form#jserp-filters input[name="geoId"]',
    "job_card": "li",
    "card_container": "[data-entity-urn]",
    "job_id": "data-entity-urn",
    "title": "h3, .base-search-card__title",
    "company": "h4, .base-search-card__subtitle",
    "location": ".job-search-card__location",
    "link": "a.base-card__full-link",
    "metadata": ".base-search-card__metadata, .job-search-card__metadata",
}

# CSS detail search selectors (job Page)
DETAIL_SELECTORS = {
    "description": "div.description__text--rich div.show-more-less-html__markup",
    "time_ago": ".posted-time-ago__text",
    # List of criteria (Seniority, Employment type, etc.)
    "criteria_list": "ul.description__job-criteria-list li.description__job-criteria-item",
    "criteria_label": ".description__job-criteria-subheader",
    "criteria_value": ".description__job-criteria-text.description__job-criteria-text--criteria",
    "criteria_value_alt": ".description__job-criteria-text",
}

# Texts for matching (avoid hardcoding in the Parser)
CRITERIA_LABELS = {
    "seniority": "Seniority level",
    "employment": "Employment type",
}
