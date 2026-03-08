FROM apache/spark-py:v3.4.0

USER root

# Download connector JARs for Kafka and Elasticsearch
RUN cd /opt/spark/jars && \
    curl -sLO https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.4.0/spark-sql-kafka-0-10_2.12-3.4.0.jar && \
    curl -sLO https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.4.0/kafka-clients-3.4.0.jar && \
    curl -sLO https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.4.0/spark-token-provider-kafka-0-10_2.12-3.4.0.jar && \
    curl -sLO https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar && \
    curl -sLO https://repo1.maven.org/maven2/org/elasticsearch/elasticsearch-spark-30_2.12/8.11.0/elasticsearch-spark-30_2.12-8.11.0.jar && \
    pip install --no-cache-dir elasticsearch==8.11.0

WORKDIR /app
COPY streaming_job.py .

CMD ["/opt/spark/bin/spark-submit", \
    "--master", "local[*]", \
    "--jars", "/opt/spark/jars/spark-sql-kafka-0-10_2.12-3.4.0.jar,/opt/spark/jars/kafka-clients-3.4.0.jar,/opt/spark/jars/spark-token-provider-kafka-0-10_2.12-3.4.0.jar,/opt/spark/jars/commons-pool2-2.11.1.jar,/opt/spark/jars/elasticsearch-spark-30_2.12-8.11.0.jar", \
    "/app/streaming_job.py"]
