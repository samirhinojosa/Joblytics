# Welcome to the Jungle's job search UI is client-side rendered, so there is
# no server-rendered search HTML to scrape and no CSS-selector dicts here
# (unlike pipelines/linkedin/constants.py). Discovery instead goes through
# WTTJ's public, robots-allowed sitemap, and per-offer data comes from a
# standard schema.org/JobPosting JSON-LD block on each detail page.

WTTJ_SITEMAP_INDEX_URL = "https://www.welcometothejungle.com/sitemaps/index.xml.gz"

# Only sitemap-index entries whose <loc> contains this are job-listing shards;
# the index also lists company-profiles/articles/... sitemaps we don't want.
JOB_LISTINGS_SHARD_MARKER = "job-listings"

JOB_POSTING_LD_TYPE = "JobPosting"

# Sitemap enumeration is unfiltered (no title/location search endpoint exists
# over plain HTTP), so a query scans shards until enough candidates are found
# or this cap is hit — bounds worst-case latency/request volume per run.
MAX_SHARDS_SCANNED_PER_QUERY = 3

# Tighter than LinkedIn's 5 workers: WTTJ's AWS WAF Bot Control challenge was
# observed to be sensitive to request volume/fingerprint during spec research.
MAX_DETAIL_ENRICHMENT_WORKERS = 3

# AWS WAF Bot Control's documented challenge response for this site is HTTP
# 202 with a non-JSON-LD/non-XML body — `requests.Response.ok` is True for
# any 2xx status, so without this, a 202 challenge is silently treated as a
# legitimate "nothing found" result instead of a retryable soft-failure.
WAF_CHALLENGE_STATUS_CODE = 202
