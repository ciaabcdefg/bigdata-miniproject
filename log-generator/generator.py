"""
Log Generator — Produces simulated microservice log events to Kafka.

Generates JSON logs for auth-service, payment-service, and api-gateway
at random intervals (configurable via LOG_INTERVAL_MIN / LOG_INTERVAL_MAX).
"""

import json
import os
import random
import time
from datetime import datetime, timezone

from kafka import KafkaProducer

# ── Configuration ──────────────────────────────────────────────────────
KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC", "service-logs")
INTERVAL_MIN = float(os.environ.get("LOG_INTERVAL_MIN", 0.05))
INTERVAL_MAX = float(os.environ.get("LOG_INTERVAL_MAX", 0.05))

# ── Log Templates ──────────────────────────────────────────────────────
SERVICES = [
    {
        "service": "auth-service",
        "scenarios": [
            {"level": "INFO",  "message": "User login successful",               "status_code": 200, "rt_range": (50, 200)},
            {"level": "INFO",  "message": "Token refreshed",                      "status_code": 200, "rt_range": (30, 100)},
            {"level": "WARN",  "message": "Multiple failed login attempts",       "status_code": 401, "rt_range": (100, 500)},
            {"level": "ERROR", "message": "Connection timeout to database",       "status_code": 500, "rt_range": (3000, 5000)},
            {"level": "ERROR", "message": "Authentication service unavailable",   "status_code": 503, "rt_range": (5000, 10000)},
        ],
    },
    {
        "service": "payment-service",
        "scenarios": [
            {"level": "INFO",  "message": "Payment processed successfully",       "status_code": 200, "rt_range": (100, 300)},
            {"level": "INFO",  "message": "Refund initiated",                     "status_code": 200, "rt_range": (150, 400)},
            {"level": "WARN",  "message": "Payment gateway slow response",        "status_code": 200, "rt_range": (2000, 4000)},
            {"level": "ERROR", "message": "Payment gateway timeout",              "status_code": 504, "rt_range": (5000, 10000)},
            {"level": "ERROR", "message": "Insufficient funds",                   "status_code": 402, "rt_range": (80, 200)},
        ],
    },
    {
        "service": "api-gateway",
        "scenarios": [
            {"level": "INFO",  "message": "Request routed successfully",          "status_code": 200, "rt_range": (20, 100)},
            {"level": "INFO",  "message": "Rate limit check passed",             "status_code": 200, "rt_range": (10, 50)},
            {"level": "WARN",  "message": "High memory usage detected",           "status_code": 200, "rt_range": (500, 1500)},
            {"level": "WARN",  "message": "Rate limit threshold approaching",     "status_code": 429, "rt_range": (10, 30)},
            {"level": "ERROR", "message": "Upstream service unreachable",          "status_code": 502, "rt_range": (5000, 10000)},
        ],
    },
]

# Weighted distribution: ~60% INFO, ~25% WARN, ~15% ERROR
LEVEL_WEIGHTS = {"INFO": 60, "WARN": 25, "ERROR": 15}


def pick_scenario():
    """Pick a random service and scenario, weighted toward INFO."""
    svc = random.choice(SERVICES)
    # Build weighted list
    weighted = []
    for s in svc["scenarios"]:
        weighted.extend([s] * LEVEL_WEIGHTS.get(s["level"], 10))
    scenario = random.choice(weighted)
    return svc["service"], scenario


def generate_log():
    """Generate a single log event as a dict."""
    service_name, scenario = pick_scenario()
    rt_min, rt_max = scenario["rt_range"]
    return {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "service": service_name,
        "level": scenario["level"],
        "message": scenario["message"],
        "response_time_ms": random.randint(rt_min, rt_max),
        "status_code": scenario["status_code"],
    }


def create_producer(retries=30, delay=5):
    """Create a Kafka producer with retry logic for startup ordering."""
    for attempt in range(1, retries + 1):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
            )
            print(f"[log-generator] Connected to Kafka at {KAFKA_BROKER}")
            return producer
        except Exception as e:
            print(f"[log-generator] Attempt {attempt}/{retries} — Kafka not ready: {e}")
            time.sleep(delay)
    raise RuntimeError(f"Could not connect to Kafka at {KAFKA_BROKER} after {retries} attempts")


def main():
    producer = create_producer()
    print(f"[log-generator] Producing to topic '{KAFKA_TOPIC}' every {INTERVAL_MIN}–{INTERVAL_MAX}s")

    try:
        while True:
            log_event = generate_log()
            producer.send(KAFKA_TOPIC, value=log_event)
            producer.flush()
            print(f"[log-generator] Sent: {json.dumps(log_event)}")
            time.sleep(random.uniform(INTERVAL_MIN, INTERVAL_MAX))
    except KeyboardInterrupt:
        print("[log-generator] Shutting down...")
    finally:
        producer.close()


if __name__ == "__main__":
    main()
