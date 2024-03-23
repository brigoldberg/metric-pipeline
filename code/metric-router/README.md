# Metric Router

The metric router does three things:
1. Consumes metrics from Redpanda Topic
1. Classifies metrics into buckets based on the metric name
1. Writes measurements to database (ClickHouse)

## Consuming from Redpanda

Uses ASYNCIO to read from Redpanda and write to a ASYNCIO queue.

## Classifying metrics

Read from ASYNCIO queue and classify each measurement by its name.  Write
message into a `measurement` object which is stored in a dict based on the 
measurement name.

## Write measurements to database

This runs as a thread and waits for either of the following conditions to
occur.
1. `measurement` metric count becomes larger than 100
1. `measurement` time since last update is gt 60 seconds

If either of these occur, the thread will write all the measurements to 
the database, empty the `measurment` record list and update the `update_time`.