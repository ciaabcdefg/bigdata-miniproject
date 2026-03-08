# Bigdata Pipeline — Real-Time Log Monitoring

A single-node Docker Compose deployment of a real-time microservice log processing pipeline.

## Architecture

```
Microservice Logs → Kafka → PySpark Structured Streaming → Elasticsearch → Kibana
                         ↘ Hive / HDFS (Data Lake)
```

## Services

| Service | Port | URL |
|---|---|---|
| Kafka | 9092 | — |
| HDFS Namenode UI | 9870 | http://localhost:9870 |
| Hive Server | 10000 | — |
| Spark Master UI | 8080 | http://localhost:8080 |
| Elasticsearch | 9200 | http://localhost:9200 |
| Kibana | 5601 | http://localhost:5601 |

## Prerequisites

- **Docker** and **Docker Compose** v2+
- **~8 GB RAM** available for Docker

## Quick Start

```powershell
# Windows
.\scripts\start.ps1

# Linux / macOS
bash scripts/start.sh
```

Or manually:

```bash
docker compose build
docker compose up -d
```

Wait ~60 seconds for all services to initialize, then open Kibana at http://localhost:5601.

## Use Cases

1. **Error Threshold per Service** — Counts ERROR-level logs per service in 10-second windows → `error-counts` ES index
2. **Request Count per Service** — Counts all requests per service in 10-second windows → `request-counts` ES index

## Kibana Setup

1. Open http://localhost:5601
2. Go to **Stack Management → Index Patterns**
3. Create patterns for `error-counts*` and `request-counts*`
4. Go to **Discover** or create dashboards

## Hive Setup

```bash
docker compose exec hive-server beeline -u jdbc:hive2://localhost:10000
```

Then run `hive/init.sql` to create the `service_logs` table.

## Stop

```powershell
# Windows
.\scripts\stop.ps1

# Linux / macOS
bash scripts/stop.sh
```

Or: `docker compose down -v`

## Project Structure

```
bigdata/
├── docker-compose.yml
├── .env
├── log-generator/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── generator.py
├── spark/
│   ├── Dockerfile
│   └── streaming_job.py
├── hive/
│   └── init.sql
└── scripts/
    ├── start.sh / start.ps1
    └── stop.sh / stop.ps1
```
