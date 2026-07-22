-- Crear la base de datos de destino para dbt
CREATE DATABASE IF NOT EXISTS ANALYTICS_DB;

-- Crear el esquema inicial de staging
CREATE SCHEMA IF NOT EXISTS ANALYTICS_DB.STAGING;
