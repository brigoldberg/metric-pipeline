# consumer.py

import asyncio
import logging
from aiokafka import AIOKafkaConsumer
from prometheus_client import Counter

logger = logging.getLogger()
module_logger = logging.getLogger('aiokafka')
module_logger.setLevel(logging.WARNING)

kafka_reads = Counter('metric_rtr_kafka_reads', 'Reads from Kafka topic')
kafka_read_bytes = Counter('metric_rtr_kafka_read_bytes', 'Sum bytes read from Kafka topics')

async def metric_consumer(msg_queue, config):
    """
    Read data from Kafka topic and add to queue.
    """
    consumer = AIOKafkaConsumer(
        config['consumer'].get('kafka_topic'),
        bootstrap_servers = config['consumer'].get('bootstrap_servers'),
        group_id = config['consumer'].get('group_id'),
    )

    await consumer.start()

    try:
        async for msg in consumer:
            kafka_reads.inc()
            kafka_read_bytes.inc(msg.serialized_value_size)

            await msg_queue.put(msg)
    finally:
        await consumer.stop()