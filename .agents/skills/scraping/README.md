# Skill: Responsible Ingestion & Scraping Policy
This skill ensures that all extraction workflows built inside `src/joblytics/infrastructure/http/scraping/` follow platform safety compliance.

## Rules
- Enforce strict progressive backoff and randomized delays between target platform network calls.
- Always implement timeout controls and failure-aware retry logic.
- Rotate headers and identifiable User-Agent strings dynamically.
- Support a functional Dry-Run mode (no live network connections) to allow seamless pipeline testing.
- Respect platform-aware crawling profiles and avoid mass automation abuse.
