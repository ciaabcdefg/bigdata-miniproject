#!/bin/bash
set -e

KIBANA_URL="http://kibana:5601"
DASHBOARD_FILE="/tmp/kibana-dashboard.ndjson"

echo "Waiting for Kibana to be ready at $KIBANA_URL..."
until curl -s "$KIBANA_URL/api/status" | grep -q '"overall":{"level":"available"'; do
  sleep 5
done
echo "Kibana is ready!"

echo "Importing Kibana index patterns and dashboard..."
curl -X POST "$KIBANA_URL/api/saved_objects/_import?createNewCopies=true" \
  -H "kbn-xsrf: true" \
  --form file=@$DASHBOARD_FILE

echo -e "\nKibana setup complete."
