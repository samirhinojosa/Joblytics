

{{ config(schema='stg') }}
-- {{ config(materialized='view') }}

/*
    Actions to make over city
    - Trim and uppercase 
    - remove '*'
    - remove empty rows
    - excluding specific cities
*/

SELECT
    TRIM(
        UPPER(
            REPLACE(city, '*', '')
        )
    ) as city
FROM dbt.cities
WHERE city IS NOT null
    AND NOT city IN (
        'England', 'Scotland', 'Wales', 'Northern Ireland')