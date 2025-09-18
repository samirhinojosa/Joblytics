{{ config(schema='stg') }}
{{ config(materialized='view') }}


SELECT company_id,
    UPPER(address) AS address,
    CAST (total_spend AS DECIMAL) AS total_spend,
    COALESCE(
        (SELECT city FROM {{ ref('stg__cities') }}
            WHERE address LIKE '%'||chr(10)||city||',%'
            ORDER BY city DESC LIMIT 1),
            'OTHER'
    ) AS city
FROM dbt.addresses
WHERE address IS NOT NULL



