-- One-time, manual setup for the Welcome to the Jungle RAW (Bronze) landing zone.
-- Not run by dbt or by the app — copy/paste into a Snowflake worksheet once.
-- The Python loader (SnowflakeRawJobOfferRepository) only PUTs + COPY INTOs;
-- it never creates these objects.

create database if not exists raw_db;

create schema if not exists raw_db.wttj;

create or replace file format raw_db.wttj.json_ff
    type = json;

create stage if not exists raw_db.wttj.joblytics_raw_stage
    file_format = raw_db.wttj.json_ff;

create table if not exists raw_db.wttj.raw_wttj_jobs (
    src_json variant,
    _loaded_at timestamp_ltz default current_timestamp(),
);
