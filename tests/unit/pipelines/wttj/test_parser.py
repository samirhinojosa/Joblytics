from pathlib import Path

from joblytics.pipelines.wttj.parser import WTTJParser

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_sitemap_index_keeps_only_job_listings_shards() -> None:
    shards = WTTJParser.parse_sitemap_index(_fixture("sitemap_index.xml"))

    assert shards == [
        "https://www.welcometothejungle.com/sitemaps/job-listings.0.xml.gz",
        "https://www.welcometothejungle.com/sitemaps/job-listings.1.xml.gz",
    ]


def test_parse_job_listing_urls_extracts_every_loc() -> None:
    urls = WTTJParser.parse_job_listing_urls(_fixture("job_listings_shard.xml"))

    assert len(urls) == 5
    assert (
        "https://www.welcometothejungle.com/fr/companies/code-busters/jobs/senior-data-engineer-h-f_paris"
        in urls
    )


def test_filter_candidate_urls_matches_title_and_location_tokens() -> None:
    urls = WTTJParser.parse_job_listing_urls(_fixture("job_listings_shard.xml"))

    candidates = WTTJParser.filter_candidate_urls(urls, "Data Engineer", "Paris")

    assert candidates == [
        "https://www.welcometothejungle.com/fr/companies/code-busters/jobs/senior-data-engineer-h-f_paris"
    ]


def test_filter_candidate_urls_excludes_partial_token_matches() -> None:
    urls = WTTJParser.parse_job_listing_urls(_fixture("job_listings_shard.xml"))

    # "Data Engineer" matches septeo/courier-health too, but "New York"/"Montpellier"
    # don't satisfy a "Paris" location filter.
    candidates = WTTJParser.filter_candidate_urls(urls, "Data Engineer", "Montpellier")

    assert candidates == [
        "https://www.welcometothejungle.com/fr/companies/septeo/jobs/data-engineer-h-f_montpellier_SEPTE_3jMzwpo"
    ]


def test_filter_candidate_urls_returns_empty_when_nothing_matches() -> None:
    urls = WTTJParser.parse_job_listing_urls(_fixture("job_listings_shard.xml"))

    candidates = WTTJParser.filter_candidate_urls(urls, "Nurse", "Berlin")

    assert candidates == []


def test_parse_job_detail_extracts_job_posting_fields() -> None:
    parser = WTTJParser()

    data = parser.parse_job_detail(_fixture("job_detail.html"))

    assert data["title"] == "Senior Data Engineer (H/F)"
    assert data["company"] == "Code Busters"
    assert data["location"] == "Courbevoie, FR"
    assert "large-scale data pipelines" in data["description"]
    assert "<strong>" in data["raw_description_html"]
    assert data["raw_contract_type"] == "FULL_TIME"
    assert data["raw_time_posted"] == "2026-07-20T08:39:03Z"
    assert data["raw"]["job_posting"]["@type"] == "JobPosting"
    assert data["raw"]["faq"]["@type"] == "FAQPage"


def test_parse_job_detail_returns_empty_dict_when_no_job_posting_block() -> None:
    parser = WTTJParser()

    data = parser.parse_job_detail(_fixture("job_detail_no_jobposting.html"))

    assert data == {}


def test_parse_job_detail_skips_empty_and_malformed_ldjson_blocks() -> None:
    parser = WTTJParser()

    data = parser.parse_job_detail(_fixture("job_detail_malformed_ldjson.html"))

    assert data["title"] == "Senior Data Engineer (H/F)"
    assert data["company"] == "Code Busters"
    assert data["location"] is None
