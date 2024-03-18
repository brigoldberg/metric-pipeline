# classifier.py

import logging
import msgpack
import time
from dataclasses import dataclass
from prometheus_client import Counter, Gauge

msg_decoded = Counter('metric_rtr_msg_decoded', 'MsgPack messages decoded')
bucket_size = Gauge('metric_rtr_bucket_size', 'Metric bucket size', ['metric_name'])
measurement_count = Gauge('metric_rtr_measurement_count', 'Active measurements')

logger = logging.getLogger()


@dataclass
class Measurement:
    name: str
    update_time: int
    metrics: list


async def metric_classifier(msg_queue, metric_bucket):

    while True:

        packed_msg = await msg_queue.get()
        msg = unpack_msg(packed_msg)
        msg_name = msg['name']

        if msg_name not in metric_bucket.keys():
            metric_bucket[msg_name] = Measurement(msg_name, time.time(), [msg,])
            logger.debug(f'Created new metric bucket: {msg_name}')
        else:
            metric_bucket[msg_name].metrics.append(msg)
            metric_bucket[msg_name].update_time = time.time()
            # logger.debug(f'Appended msg to metric bucket {msg_name}')

        bucket_size.labels(msg_name).set(len(metric_bucket[msg_name].metrics))
        measurement_count.set(len(metric_bucket))
            

def unpack_msg(msg):
    # DeSerialize MsgPack data
    try:
        unpacked_metric = msgpack.unpackb(msg.value)
        msg_decoded.inc()
        return unpacked_metric
    except Exception as e:
        logger.warning(f'Error upacking message: {e}')
        return None