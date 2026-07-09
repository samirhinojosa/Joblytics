# Skill: Clean Architecture Validator
This skill enforces that the `src/joblytics/domain/` directory remains completely pure.

## Rules
- NO external HTTP libraries (requests, httpx).
- NO database connectors or drivers (sqlalchemy, psycopg, snowflake).
- NO infrastructure references.

## Execution
Run code verification before finalizing domain tasks to ensure compliance.
