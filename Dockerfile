FROM python:3.9.13-slim-buster
RUN pip install msgpack clickhouse-driver confluent-kafka kafka-python aiokafka
RUN mkdir -p /app
WORKDIR /app
CMD ["python3", "metric-router.py"]