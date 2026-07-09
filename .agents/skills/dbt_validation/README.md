# Skill: dbt & Snowflake Standards Validator
This skill ensures that all SQL and dbt models match production standards before staging data.

## Rules
- Every model must have a matching entry in a `.yml` file.
- All subqueries must use CTEs (Common Table Expressions).
- SQL keywords must be lowercase.
