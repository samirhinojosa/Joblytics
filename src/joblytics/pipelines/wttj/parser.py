import json
import logging
import unicodedata
from typing import Any
from urllib.parse import urlparse
from xml.etree import ElementTree

from bs4 import BeautifulSoup

from .constants import JOB_LISTINGS_SHARD_MARKER, JOB_POSTING_LD_TYPE

_SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def _normalize(value: str) -> str:
    """Lowercase and strip accents, for locale-insensitive slug matching."""
    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return without_accents.lower()


class WTTJParser:
    """
    Responsible for extracting structured data from raw XML/HTML text.
    Does not perform network requests.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("joblytics")

    @staticmethod
    def parse_sitemap_index(xml_text: str) -> list[str]:
        """
        Extract job-listing shard URLs from the sitemap index.

        Args:
            xml_text (str): Raw sitemap index XML.

        Returns:
            list[str]: URLs of shards whose name matches
                JOB_LISTINGS_SHARD_MARKER (e.g. job-listings.0.xml.gz).
        """
        root = ElementTree.fromstring(xml_text)
        locs = [
            node.text.strip()
            for node in root.findall(".//sm:loc", _SITEMAP_NS)
            if node.text
        ]
        return [loc for loc in locs if JOB_LISTINGS_SHARD_MARKER in loc]

    @staticmethod
    def parse_job_listing_urls(xml_text: str) -> list[str]:
        """
        Extract job detail URLs from a job-listings sitemap shard.

        Args:
            xml_text (str): Raw sitemap shard XML.

        Returns:
            list[str]: Job detail page URLs.
        """
        root = ElementTree.fromstring(xml_text)
        return [
            node.text.strip()
            for node in root.findall(".//sm:loc", _SITEMAP_NS)
            if node.text
        ]

    @staticmethod
    def filter_candidate_urls(urls: list[str], title: str, location: str) -> list[str]:
        """
        Best-effort candidate filtering by matching title/location tokens
        against each URL's slug (path).

        This is not a real filtered search: WTTJ exposes no server-side
        search endpoint reachable over plain HTTP, so precision/recall here
        are weaker than a real search would provide.

        Args:
            urls (list[str]): Candidate job detail URLs.
            title (str): Job title query.
            location (str): Job location query.

        Returns:
            list[str]: URLs whose slug contains every whitespace-separated
                token from both title and location (case/accent-insensitive).
        """
        title_tokens = _normalize(title).split()
        location_tokens = _normalize(location).split()
        tokens = title_tokens + location_tokens

        matches = []
        for url in urls:
            slug = _normalize(urlparse(url).path.replace("-", " ").replace("_", " "))
            if all(token in slug for token in tokens):
                matches.append(url)
        return matches

    def parse_job_detail(self, html: str) -> dict[str, Any]:
        """
        Extract job posting data from a detail page's JSON-LD blocks.

        Args:
            html (str): Raw detail page HTML.

        Returns:
            dict[str, Any]: Parsed fields (title, company, location,
                description, raw_description_html, raw_contract_type,
                raw_time_posted) plus a `raw` dict holding the unmodified
                JobPosting/FAQPage JSON-LD payloads for lossless landing in
                the Bronze layer. Empty dict if no JobPosting block is found.
        """
        soup = BeautifulSoup(html, "html.parser")
        job_posting: dict[str, Any] | None = None
        faq_page: dict[str, Any] | None = None

        for tag in soup.select('script[type="application/ld+json"]'):
            if not tag.string:
                continue
            try:
                data = json.loads(tag.string)
            except json.JSONDecodeError:
                continue

            if data.get("@type") == JOB_POSTING_LD_TYPE:
                job_posting = data
            elif data.get("@type") == "FAQPage":
                faq_page = data

        if job_posting is None:
            self.logger.warning(
                "Skipping offer: no JobPosting JSON-LD block found on detail page."
            )
            return {}

        organization = job_posting.get("hiringOrganization") or {}
        locations = job_posting.get("jobLocation") or []
        address = (locations[0].get("address") if locations else None) or {}
        description_html = job_posting.get("description")

        return {
            "title": job_posting.get("title"),
            "company": organization.get("name"),
            "location": _format_location(address),
            "description": BeautifulSoup(description_html, "html.parser").get_text(
                separator="\n", strip=True
            )
            if description_html
            else None,
            "raw_description_html": description_html,
            "raw_contract_type": job_posting.get("employmentType"),
            "raw_time_posted": job_posting.get("datePosted"),
            "raw": {"job_posting": job_posting, "faq": faq_page},
        }


def _format_location(address: dict[str, Any]) -> str | None:
    parts = [address.get("addressLocality"), address.get("addressCountry")]
    formatted = ", ".join(p for p in parts if p)
    return formatted or None
