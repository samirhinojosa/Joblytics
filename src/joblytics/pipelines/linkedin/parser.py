import logging
import re
from bs4 import BeautifulSoup
from typing import Any
from .constants import SUMMARY_SELECTORS, DETAIL_SELECTORS, CRITERIA_LABELS


class LinkedInParser:
    """
    Responsible for extracting structured data from raw HTML.
    Does not perform network requests.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("joblytics")

    @staticmethod
    def parse_job_count(html: str) -> int:
        """
        Extracts the total number of jobs found from the search header.
        """
        soup = BeautifulSoup(html, "html.parser")
        node = soup.select_one(SUMMARY_SELECTORS["job_count"])
        if not node:
            return 0

        count_text = node.get_text(strip=True)
        # Remove any non-numeric characters (e.g., '10,000+' -> '10000')
        digits = re.sub(r"\D+", "", count_text)
        return int(digits) if digits else 0

    @staticmethod
    def parse_geo_id(html: str) -> int | None:
        """
        Extract the LinkedIn-specific geographic identifier (geoId) value from
        the filter form.

        Returns None if not found.
        """
        soup = BeautifulSoup(html, "html.parser")
        node = soup.select_one(SUMMARY_SELECTORS["geo_id_input"])
        if not node:
            return None

        val = node.get("value")
        if isinstance(val, str) and val.isdigit():
            return int(val)
        return None

    def parse_summary_cards(self, html: str) -> list[dict[str, Any]]:
        """
        Parses the search results list.
        Distinguishes between mandatory and optional fields.
        """

        soup = BeautifulSoup(html, "html.parser")
        cards: list[dict[str, Any]] = []

        for li in soup.select(SUMMARY_SELECTORS["job_card"]):
            # Mandatory ID Container
            container = li.select_one(SUMMARY_SELECTORS["card_container"])
            if not container:
                continue

            raw_urn = container.get(SUMMARY_SELECTORS["job_id"])
            if not isinstance(raw_urn, str):
                continue
            job_id = raw_urn.split(":")[-1]

            # Extract Nodes
            title_node = li.select_one(SUMMARY_SELECTORS["title"])
            company_node = li.select_one(SUMMARY_SELECTORS["company"])
            link_node = li.select_one(SUMMARY_SELECTORS["link"])
            location_node = li.select_one(SUMMARY_SELECTORS["location"])
            metadata_node = li.select_one(SUMMARY_SELECTORS["metadata"])

            # If these are missing, the offer is useless.
            if not (title_node and company_node and link_node):
                self.logger.warning(
                    "Skipping offer: essential data is missing (title, company or link)."
                )
                continue

            # Safe URL Extraction
            raw_url = link_node.get("href")
            if not isinstance(raw_url, str):
                continue
            clean_url = raw_url.split("?")[0]

            # Optional Fields with Defaults (Resilience)
            location = (
                location_node.get_text(strip=True) if location_node else "Not specified"
            )

            raw_work_modality = "On-site"  # Default
            if metadata_node:
                meta_text = metadata_node.get_text(strip=True).lower()
                if "remote" in meta_text or "remoto" in meta_text:
                    raw_work_modality = "Remote"
                elif "hybrid" in meta_text or "híbrido" in meta_text:
                    raw_work_modality = "Hybrid"

            cards.append(
                {
                    "provider_job_id": job_id,
                    "url": clean_url,
                    "title": title_node.get_text(strip=True),
                    "company": company_node.get_text(strip=True),
                    "location": location,
                    "raw_work_modality": raw_work_modality,
                }
            )

        return cards

    def parse_job_details(self, html: str) -> dict[str, Any]:
        """
        Parses the rich description and criteria from a specific job page.
        """
        soup = BeautifulSoup(html, "html.parser")
        data: dict[str, Any] = {
            "description": None,
            "raw_description_html": None,
            "raw_seniority": None,
            "raw_contract_type": None,
            "raw_time_posted": None,
        }

        # Main description
        desc_node = soup.select_one(DETAIL_SELECTORS["description"])
        if desc_node:
            data["description"] = desc_node.get_text(separator="\n", strip=True)
            data["raw_description_html"] = str(desc_node)

        # Time posted
        time_node = soup.select_one(DETAIL_SELECTORS["time_ago"])
        if time_node:
            data["raw_time_posted"] = time_node.get_text(strip=True)

        # Dynamic Criteria (Seniority, Employment Type)
        for li in soup.select(DETAIL_SELECTORS["criteria_list"]):
            label_node = li.select_one(DETAIL_SELECTORS["criteria_label"])
            val_node = li.select_one(
                DETAIL_SELECTORS["criteria_value"]
            ) or li.select_one(DETAIL_SELECTORS["criteria_value_alt"])

            if label_node and val_node:
                label = label_node.get_text(strip=True)
                val = val_node.get_text(strip=True)

                if label == CRITERIA_LABELS["seniority"]:
                    data["raw_seniority"] = val
                elif label == CRITERIA_LABELS["employment"]:
                    data["raw_contract_type"] = val

        return data
