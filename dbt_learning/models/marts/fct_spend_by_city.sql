{{ config(materialized='table') }}

SELECT city,
    SUM(total_spend)
FROM {{ ref('stg__addresses')}}
GROUP BY city, total_spend
ORDER BY total_spend DESC