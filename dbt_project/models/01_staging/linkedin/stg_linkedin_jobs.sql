-- View model: Cleans, casts, and deduplicates raw LinkedIn payloads
with source_data as (

    select
        src_json,
        _loaded_at
    from {{ source('linkedin', 'raw_linkedin_jobs') }}

),

renamed_data as (

    select
        src_json:provider::varchar as provider_name,
        src_json:provider_job_id::varchar as provider_job_id,
        src_json:url::varchar as job_url,
        src_json:title::varchar as job_title,
        src_json:company::varchar as company_name,
        src_json:location::varchar as raw_location,
        src_json:description::varchar as job_description,
        src_json:scraped_at::timestamp_ntz as scraped_at,
        src_json:raw_work_modality::varchar as raw_work_modality,
        src_json:raw_contract_type::varchar as raw_contract_type,
        src_json:raw_seniority::varchar as raw_seniority,
        src_json:raw_time_posted::varchar as raw_time_posted,
        src_json:raw_description_html::varchar as raw_description_html,
        src_json:search_title::varchar as search_title,
        src_json:search_location::varchar as search_location,
        src_json:search_work_modality::varchar as search_work_modality,
        src_json:search_time_posted::varchar as search_time_posted,
        src_json:raw as raw_extra,
        coalesce(src_json:file_name::varchar, null) as file_name,
        _loaded_at as extracted_at
    from source_data

),

deduplicated_data as (

    select
        *,
        {{ parse_linkedin_relative_time('raw_time_posted', 'extracted_at') }} as time_posted_at
    from renamed_data
    qualify row_number() over (
        partition by provider_job_id
        order by extracted_at desc
    ) = 1

)

select * from deduplicated_data
