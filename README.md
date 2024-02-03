# Metric Pipeline

A wireframe of a standard metric pipeline.

The pipeline consists of four (4) elements:
1. Metric publisher - Telegraf
2. Messagebus - Redpanda
3. Metric router - Python script
4. Data store - ClickHouse

# Components

### Metric Publisher

We use Telegraf to generate system metrics and publish them to Redpanda
via the Kafka output.

### Message Bus

We use Redpanda as our pub/sub app where publishers can send metrics and
where the Metric Router can consume.

Future improvements will include batching to improve the efficiency of the
database writes.

### Metric Router

The Metric Router is a simple Python implementation using AsyncIO to consume
from Redpanda and publish to ClickHouse.

### Data Store

We use ClickHouse to store our time series metric data. Its just faster than
InfluxDB and the Grafana integration is very workable.