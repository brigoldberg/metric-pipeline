FROM python:3.9.13-slim-buster
RUN apt-get -y update; apt-get -y install curl
RUN pip install msgpack clickhouse-driver confluent-kafka kafka-python aiokafka prometheus-client
ADD entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh; mkdir -p /app
ENTRYPOINT ["/entrypoint.sh"]