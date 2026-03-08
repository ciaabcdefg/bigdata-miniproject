"""
PySpark Structured Streaming Job — Real-time Log Monitoring

Reads JSON log events from Kafka, computes two streaming aggregations
in 10-second tumbling windows, and writes results to Elasticsearch.

Use Case 1: Error count per service  → ES index: error-counts
Use Case 2: Request count per service → ES index: request-counts
"""

import os
import json
import urllib.request
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, date_format, from_json, window,
)
from pyspark.sql.types import (
    IntegerType, StringType, StructField, StructType,
)

# ── Configuration ──────────────────────────────────────────────────────
KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "service-logs")
ES_HOST = os.environ.get("ES_HOST", "elasticsearch")
ES_PORT = os.environ.get("ES_PORT", "9200")
ES_ERROR_INDEX = os.environ.get("ES_ERROR_INDEX", "error-counts")
ES_REQUEST_INDEX = os.environ.get("ES_REQUEST_INDEX", "request-counts")

# ── Schema ─────────────────────────────────────────────────────────────
LOG_SCHEMA = StructType([
    StructField("timestamp", StringType(), True),
    StructField("service", StringType(), True),
    StructField("level", StringType(), True),
    StructField("message", StringType(), True),
    StructField("response_time_ms", IntegerType(), True),
    StructField("status_code", IntegerType(), True),
])


def write_to_es(batch_df, batch_id, index_name):
    """Write a micro-batch DataFrame to Elasticsearch."""
    if batch_df.count() == 0:
        return
    (
        batch_df.write
        .format("org.elasticsearch.spark.sql")
        .option("es.nodes", ES_HOST)
        .option("es.port", ES_PORT)
        .option("es.resource", index_name)
        .option("es.nodes.wan.only", "true")
        .mode("append")
        .save()
    )


def init_es_templates():
    """Create ES index templates so window_start/window_end are mapped as date."""
    es_url = f"http://{ES_HOST}:{ES_PORT}"
    templates = {
        "error-counts-template": {
            "index_patterns": ["error-counts*"],
            "template": {
                "mappings": {
                    "properties": {
                        "window_start": {"type": "date"},
                        "window_end": {"type": "date"},
                        "error_count": {"type": "integer"},
                        "service": {"type": "keyword"},
                    }
                }
            },
        },
        "request-counts-template": {
            "index_patterns": ["request-counts*"],
            "template": {
                "mappings": {
                    "properties": {
                        "window_start": {"type": "date"},
                        "window_end": {"type": "date"},
                        "request_count": {"type": "integer"},
                        "service": {"type": "keyword"},
                    }
                }
            },
        },
    }
    for name, body in templates.items():
        try:
            req = urllib.request.Request(
                f"{es_url}/_index_template/{name}",
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="PUT",
            )
            urllib.request.urlopen(req)
            print(f"[spark-streaming] Created ES template: {name}")
        except Exception as e:
            print(f"[spark-streaming] Warning: could not create template {name}: {e}")

    # Delete old indices with wrong mapping (long instead of date)
    for idx in [ES_ERROR_INDEX, ES_REQUEST_INDEX]:
        try:
            req = urllib.request.Request(f"{es_url}/{idx}", method="DELETE")
            urllib.request.urlopen(req)
            print(f"[spark-streaming] Deleted old index: {idx}")
        except Exception:
            pass  # index may not exist yet


def main():
    init_es_templates()

    spark = (
        SparkSession.builder
        .appName("RealtimeLogMonitoring")
        .config("spark.jars.packages", "")
        .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    # ── Read from Kafka ────────────────────────────────────────────────
    raw_stream = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BROKER)
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", "latest")
        .option("failOnDataLoss", "false")
        .load()
    )

    # Parse JSON value from Kafka
    parsed = (
        raw_stream
        .selectExpr("CAST(value AS STRING) as json_str")
        .select(from_json(col("json_str"), LOG_SCHEMA).alias("data"))
        .select("data.*")
        .withColumn("event_time", col("timestamp").cast("timestamp"))
    )

    # ── Use Case 1: Error Count per Service (10s window) ──────────────
    error_counts = (
        parsed
        .filter(col("level") == "ERROR")
        .withWatermark("event_time", "20 seconds")
        .groupBy(
            window(col("event_time"), "10 seconds"),
            col("service"),
        )
        .agg(count("*").alias("error_count"))
        .select(
            date_format(col("window.start"), "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'").alias("window_start"),
            date_format(col("window.end"), "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'").alias("window_end"),
            col("service"),
            col("error_count"),
        )
    )

    error_query = (
        error_counts.writeStream
        .outputMode("update")
        .foreachBatch(lambda df, bid: write_to_es(df, bid, ES_ERROR_INDEX))
        .option("checkpointLocation", "/tmp/checkpoint/errors")
        .trigger(processingTime="10 seconds")
        .start()
    )

    # ── Use Case 2: Request Count per Service (10s window) ────────────
    request_counts = (
        parsed
        .withWatermark("event_time", "20 seconds")
        .groupBy(
            window(col("event_time"), "10 seconds"),
            col("service"),
        )
        .agg(count("*").alias("request_count"))
        .select(
            date_format(col("window.start"), "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'").alias("window_start"),
            date_format(col("window.end"), "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'").alias("window_end"),
            col("service"),
            col("request_count"),
        )
    )

    request_query = (
        request_counts.writeStream
        .outputMode("update")
        .foreachBatch(lambda df, bid: write_to_es(df, bid, ES_REQUEST_INDEX))
        .option("checkpointLocation", "/tmp/checkpoint/requests")
        .trigger(processingTime="10 seconds")
        .start()
    )

    print("[spark-streaming] Streaming started — waiting for data...")
    spark.streams.awaitAnyTermination()


if __name__ == "__main__":
    main()
