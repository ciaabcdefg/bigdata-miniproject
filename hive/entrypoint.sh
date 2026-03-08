#!/bin/bash
set -e

export HIVE_CONF_DIR=/opt/hive/conf
export HADOOP_CLIENT_OPTS=" -Xmx1G $SERVICE_OPTS"

echo "[hive-metastore] Initializing schema (dbType=$DB_DRIVER)..."
if /opt/hive/bin/schematool -dbType "$DB_DRIVER" -initSchema 2>&1; then
    echo "[hive-metastore] Schema initialized successfully."
elif /opt/hive/bin/schematool -dbType "$DB_DRIVER" -info 2>&1 | grep -q "Metastore schema version"; then
    echo "[hive-metastore] Schema already exists — skipping initialization."
else
    echo "[hive-metastore] WARNING: Schema init failed. Attempting to continue..."
fi

echo "[hive-metastore] Starting Hive Metastore service..."
exec /opt/hive/bin/hive --service metastore
