#!/bin/bash
# Stop the bigdata pipeline and clean up
set -e

echo "Stopping all services..."
cd "$(dirname "$0")/.."
docker compose down -v
echo "All services stopped and volumes removed."
