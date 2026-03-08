.PHONY: build up down restart logs status clean kafka-topics kafka-consume es-check hive-shell

# ==================== Core Commands ====================

build:  ## Build custom images
	docker compose build

up: build  ## Start all services
	docker compose up -d

down:  ## Stop all services
	docker compose stop

restart: down up  ## Restart all services

clean:  ## Stop and remove all data volumes
	docker compose down -v

logs:  ## Follow logs for all services
	docker compose logs -f

status:  ## Show service statuses
	docker compose ps

# ==================== Debugging ====================

kafka-topics:  ## List Kafka topics
	docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

kafka-consume:  ## Consume 5 messages from service-logs topic
	docker compose exec kafka kafka-console-consumer \
		--bootstrap-server localhost:9092 \
		--topic service-logs \
		--max-messages 5

es-check:  ## Check Elasticsearch cluster health + indices
	@echo "=== Cluster Health ==="
	curl -s http://localhost:9200/_cluster/health?pretty
	@echo "\n=== Indices ==="
	curl -s http://localhost:9200/_cat/indices?v

es-errors:  ## Query latest error counts from Elasticsearch
	curl -s http://localhost:9200/error-counts/_search?pretty&size=5

es-requests:  ## Query latest request counts from Elasticsearch
	curl -s http://localhost:9200/request-counts/_search?pretty&size=5

hive-shell:  ## Open Hive Beeline shell
	docker compose exec hive-server beeline -u jdbc:hive2://localhost:10000

spark-ui:  ## Open Spark Master UI URL
	@echo "http://localhost:8080"

# ==================== Individual Services ====================

logs-%:  ## Follow logs for a specific service (e.g. make logs-kafka)
	docker compose logs -f $*

restart-%:  ## Restart a specific service (e.g. make restart-spark-streaming)
	docker compose restart $*

# ==================== Help ====================

help:  ## Show this help
	@grep -E '^[a-zA-Z_%-]+:.*##' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
