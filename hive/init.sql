-- Hive: Create external table for service logs stored in HDFS
-- This table maps to JSON log data consumed from Kafka

CREATE DATABASE IF NOT EXISTS logs_db;

USE logs_db;

CREATE EXTERNAL TABLE IF NOT EXISTS service_logs (
    `timestamp`        STRING    COMMENT 'ISO 8601 timestamp of the log event',
    service            STRING    COMMENT 'Name of the microservice',
    level              STRING    COMMENT 'Log level: INFO, WARN, ERROR',
    message            STRING    COMMENT 'Log message body',
    response_time_ms   INT       COMMENT 'Response time in milliseconds',
    status_code        INT       COMMENT 'HTTP status code'
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS TEXTFILE
LOCATION '/user/hive/warehouse/service_logs';
