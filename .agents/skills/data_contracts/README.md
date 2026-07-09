# Skill: Data Contracts & Staging Schemas
This skill validates ingestion outputs to guarantee seamless loading into Snowflake variant or structured columns.

## Rules
- Schema must comply with the target Snowflake table ingestion structure.
- Datetime fields must follow ISO 8601 string format before S3 upload.
