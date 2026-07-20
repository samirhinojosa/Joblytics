from joblytics.pipelines.linkedin.parser import LinkedInParser


# --- parse_job_count ---


def test_parse_job_count_extracts_digits_from_comma_separated_text() -> None:
    html = '<span class="results-context-header__job-count">10,000+ results</span>'
    assert LinkedInParser.parse_job_count(html) == 10000


def test_parse_job_count_returns_zero_when_node_missing() -> None:
    assert LinkedInParser.parse_job_count("<div>nothing here</div>") == 0


def test_parse_job_count_returns_zero_when_text_has_no_digits() -> None:
    html = '<span class="results-context-header__job-count">many</span>'
    assert LinkedInParser.parse_job_count(html) == 0


# --- parse_geo_id ---


def test_parse_geo_id_returns_int_when_present_and_numeric() -> None:
    html = '<form id="jserp-filters"><input name="geoId" value="102277331"/></form>'
    assert LinkedInParser.parse_geo_id(html) == 102277331


def test_parse_geo_id_returns_none_when_value_not_digit() -> None:
    html = '<form id="jserp-filters"><input name="geoId" value="abc"/></form>'
    assert LinkedInParser.parse_geo_id(html) is None


def test_parse_geo_id_returns_none_when_node_missing() -> None:
    assert LinkedInParser.parse_geo_id("<div>nothing</div>") is None


# --- parse_summary_cards ---


def _card_html(
    *,
    urn: str = "urn:li:jobPosting:123456",
    title: str = "Data Engineer",
    company: str = "Acme",
    href: str = "https://www.linkedin.com/jobs/view/123456?trk=xyz",
    location: str | None = "Paris, France",
    metadata: str | None = "Remote",
) -> str:
    location_html = (
        f'<span class="job-search-card__location">{location}</span>' if location else ""
    )
    metadata_html = (
        f'<div class="base-search-card__metadata">{metadata}</div>' if metadata else ""
    )
    return f"""
    <ul>
      <li>
        <div data-entity-urn="{urn}">
          <h3 class="base-search-card__title">{title}</h3>
          <h4 class="base-search-card__subtitle">{company}</h4>
          {location_html}
          <a class="base-card__full-link" href="{href}">link</a>
          {metadata_html}
        </div>
      </li>
    </ul>
    """


def test_parse_summary_cards_extracts_full_card() -> None:
    cards = LinkedInParser().parse_summary_cards(_card_html())

    assert len(cards) == 1
    card = cards[0]
    assert card["provider_job_id"] == "123456"
    assert card["url"] == "https://www.linkedin.com/jobs/view/123456"
    assert card["title"] == "Data Engineer"
    assert card["company"] == "Acme"
    assert card["location"] == "Paris, France"
    assert card["raw_work_modality"] == "Remote"


def test_parse_summary_cards_skips_card_missing_mandatory_fields() -> None:
    html = """
    <ul>
      <li>
        <div data-entity-urn="urn:li:jobPosting:1"></div>
      </li>
    </ul>
    """
    assert LinkedInParser().parse_summary_cards(html) == []


def test_parse_summary_cards_skips_card_without_container() -> None:
    html = "<ul><li>No data-entity-urn here</li></ul>"
    assert LinkedInParser().parse_summary_cards(html) == []


def test_parse_summary_cards_skips_card_when_link_has_no_href() -> None:
    html = """
    <ul>
      <li>
        <div data-entity-urn="urn:li:jobPosting:1">
          <h3 class="base-search-card__title">Data Engineer</h3>
          <h4 class="base-search-card__subtitle">Acme</h4>
          <a class="base-card__full-link">no href here</a>
        </div>
      </li>
    </ul>
    """
    assert LinkedInParser().parse_summary_cards(html) == []


def test_parse_summary_cards_defaults_location_and_modality() -> None:
    html = _card_html(location=None, metadata=None)
    cards = LinkedInParser().parse_summary_cards(html)

    assert cards[0]["location"] == "Not specified"
    assert cards[0]["raw_work_modality"] == "On-site"


def test_parse_summary_cards_detects_hybrid_modality() -> None:
    html = _card_html(metadata="Paris, France (Hybrid)")
    cards = LinkedInParser().parse_summary_cards(html)
    assert cards[0]["raw_work_modality"] == "Hybrid"


# --- parse_job_details ---

DETAILS_HTML = """
<div class="description__text--rich">
  <div class="show-more-less-html__markup">
    <p>Line one</p><p>Line two</p>
  </div>
</div>
<span class="posted-time-ago__text">3 days ago</span>
<ul class="description__job-criteria-list">
  <li class="description__job-criteria-item">
    <h3 class="description__job-criteria-subheader">Seniority level</h3>
    <span class="description__job-criteria-text description__job-criteria-text--criteria">Mid-Senior level</span>
  </li>
  <li class="description__job-criteria-item">
    <h3 class="description__job-criteria-subheader">Employment type</h3>
    <span class="description__job-criteria-text description__job-criteria-text--criteria">Full-time</span>
  </li>
  <li class="description__job-criteria-item">
    <h3 class="description__job-criteria-subheader">Industries</h3>
    <span class="description__job-criteria-text description__job-criteria-text--criteria">Software</span>
  </li>
</ul>
"""


def test_parse_job_details_extracts_description_time_and_criteria() -> None:
    data = LinkedInParser().parse_job_details(DETAILS_HTML)

    assert data["description"] == "Line one\nLine two"
    assert data["raw_description_html"] is not None
    assert data["raw_time_posted"] == "3 days ago"
    assert data["raw_seniority"] == "Mid-Senior level"
    assert data["raw_contract_type"] == "Full-time"


def test_parse_job_details_falls_back_to_alt_value_selector() -> None:
    html = """
    <ul class="description__job-criteria-list">
      <li class="description__job-criteria-item">
        <h3 class="description__job-criteria-subheader">Seniority level</h3>
        <span class="description__job-criteria-text">Junior</span>
      </li>
    </ul>
    """
    data = LinkedInParser().parse_job_details(html)
    assert data["raw_seniority"] == "Junior"


def test_parse_job_details_returns_all_none_for_empty_page() -> None:
    data = LinkedInParser().parse_job_details("<html><body></body></html>")
    assert data == {
        "description": None,
        "raw_description_html": None,
        "raw_seniority": None,
        "raw_contract_type": None,
        "raw_time_posted": None,
    }
