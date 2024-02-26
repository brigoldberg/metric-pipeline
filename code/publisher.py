# publisher.py

import asyncio
import json
import logging
import msgpack
import time
from clickhouse_driver import Client
from dataclasses import dataclass
from prometheus_client import Counter, Gauge

logger = logging.getLogger()

CH_PORT = 9000

msg_decoded = Counter('metric_rtr_msg_decoded', 'MsgPack messages decoded')
db_inserts = Counter('metric_rtr_db_inserts', 'Database inserts')
bucket_size = Gauge('metric_rtr_bucket_size', 'Metric bucket size', ['metric_name'])

metrics = {}

@dataclass
class Metric:
    name: str
    update_time: int
    metric_rows: list

async def metric_writer(msg_queue, args):

    ch_client = Client(host=args.ch_host, port=CH_PORT)    

    bucket_check_counter = 0

    while True:

        packed_msg = await msg_queue.get()
        msg = unpack_msg(packed_msg)
        msg_name = msg['name']

        if msg_name not in metrics.keys():
            metrics[msg_name] = Metric(msg_name, time.time(), [msg,])
            logger.debug(f"Created new bucket: {msg_name}")
        else:
            metrics[msg_name].metric_rows.append(msg)

        # Cycle thru all metrics objects and process if length > 10 or update time > 1 min.
        if bucket_check_counter % 100 == 0:

            for k in metrics.keys():

                time_now = time.time()
                bucket_size.labels(k).set(len(metrics[k].metric_rows))
                
                if (time_now - metrics[k].update_time) > 60:
                    write_metrics(metrics[k], ch_client)
                elif len(metrics[k].metric_rows) > 10:
                    write_metrics(metrics[k], ch_client)

        bucket_check_counter += 1

def write_metrics(metric, ch_client):
    # Clear rows and reset timestamp
    columns = []
    for j in metric.metric_rows:
        columns.append({**j['tags'], **j['fields'], 'ts': int(j['time'].to_unix())})
    json_cols = json.dumps(columns)
    sql_cmd = f'INSERT INTO {metric.name} FORMAT JSONEachRow {json_cols}'
    ch_client.execute(sql_cmd)  
    db_inserts.inc()
    
    metric.metric_rows.clear()
    metric.update_time = time.time()
    logger.debug(f'Clear and timestamp Metric: {metric.name}')

def unpack_msg(msg):
    # DeSerialize MsgPack data
    try:
        unpacked_metric = msgpack.unpackb(msg.value)
        msg_decoded.inc()
        return unpacked_metric
    except Exception as e:
        logger.warning(f'Error upacking message: {e}')
        return None
