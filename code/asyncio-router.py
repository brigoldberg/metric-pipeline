#!/usr/bin/env python3
"""
Pub/Sub using Python ASYNCIO module.
"""

import argparse
import asyncio
import json
import logging
import msgpack
from aiokafka import AIOKafkaConsumer
from clickhouse_driver import Client
from prometheus_client import Counter, start_http_server

CH_PORT = 9000
KAFKA_PORT = 9092

kafka_reads = Counter('kafka_reads', 'Reads from Kafka topic')
msgs_decoded = Counter('messages_upacked', 'Messages decoded from msgpack')
db_inserts = Counter('db_inserts', 'Database inserts')

def cli_args():
    parser = argparse.ArgumentParser(description='Metric Router')
    parser.add_argument('-v', dest='verbose', action='store_true')
    parser.add_argument('-i', dest='info_logging', action='store_true')
    parser.add_argument('-c', dest='ch_host', action='store', default='clickhouse')
    parser.add_argument('-b', dest='bootstrap_server', action='store', default='redpanda:9092')
    parser.add_argument('-t', dest='kafka_topic', action='store', default='telegraf')
    return parser.parse_args()

def get_logger(args):
    logger = logging.getLogger()
    if args.verbose:
        logging.basicConfig(format='%(levelname)s - %(message)s',level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s - %(message)s',level=logging.WARNING)
    return logger

async def kafka_consumer(msg_queue, args):
    # Read data from Kafka and put message into queue
    consumer = AIOKafkaConsumer(
        args.kafka_topic,
        bootstrap_servers = args.bootstrap_server,
        group_id = "metrics",
    )

    await consumer.start()

    try:
        async for msg in consumer:
            logger.debug(f"Putting msg in queue: {msg}")
            kafka_reads.inc()
            await msg_queue.put(msg)
    finally:
        await consumer.stop()

async def queue_reader(msg_queue, args):
    # Read from queue, deserialize and insert into db
    ch_client = Client(host=args.ch_host, port=CH_PORT)
    while True:
        packed_msg = await msg_queue.get()
        unpacked_msg = unpack_msg(packed_msg)
        msgs_decoded.inc()
        insert_db(ch_client, unpacked_msg)

def unpack_msg(msg):
    # DeSerialize MsgPack data
    try:
        unpacked_metric = msgpack.unpackb(msg.value)
        return unpacked_metric
    except Exception as e:
        logger.warning(f'Error upacking message: {e}')
        return None

def insert_db(ch_client, metric_line):
    # Insert data into ClickHouse DB
    columns = {**metric_line['tags'], **metric_line['fields'], 'ts': int(metric_line['time'].to_unix())}
    json_cols = json.dumps(columns)
    sql_cmd = f'INSERT INTO {metric_line["name"]} FORMAT JSONEachRow {json_cols}'
    logger.debug(f'SQL CMD: {sql_cmd}')

    ch_client.execute(sql_cmd)  
    db_inserts.inc()

async def main(args):

    msg_queue = asyncio.Queue()

    kafka_task = asyncio.create_task(kafka_consumer(msg_queue, args))
    queue_task = asyncio.create_task(queue_reader(msg_queue, args))

    await asyncio.gather(kafka_task, queue_task)


if __name__ == '__main__':

    args = cli_args()
    logger = get_logger(args)
    start_http_server(8000)

    module_logger = logging.getLogger('aiokafka')
    module_logger.setLevel(logging.WARNING)

    asyncio.run(main(args))