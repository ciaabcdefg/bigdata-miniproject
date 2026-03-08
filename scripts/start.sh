#!/bin/bash
# Start the bigdata pipeline
set -e

echo "=========================================="
echo "  Bigdata Pipeline — Starting All Services"
echo "=========================================="

cd "$(dirname "$0")/.."

echo "[1/3] Building custom images..."
docker compose build

echo "[2/3] Starting all services..."
docker compose up -d

echo "[3/3] Waiting for services to be healthy..."
echo ""

# Wait for key services
services=("zookeeper" "kafka" "namenode" "elasticsearch")
for svc in "${services[@]}"; do
    printf "  Waiting for %-20s" "$svc..."
    until docker compose ps "$svc" 2>/dev/null | grep -q "healthy"; do
        sleep 2
    done
    echo "✓ ready"
done

echo ""
echo "=========================================="
echo "  All services are up!"
echo ""
echo "  Kafka:          localhost:9092"
echo "  HDFS Namenode:  http://localhost:9870"
echo "  Spark UI:       http://localhost:8080"
echo "  Elasticsearch:  http://localhost:9200"
echo "  Kibana:         http://localhost:5601"
echo "  Hive Server:    localhost:10000"
echo "=========================================="
echo ""
echo "  View logs: docker compose logs -f"
echo "  Stop:      docker compose down"
echo "=========================================="
