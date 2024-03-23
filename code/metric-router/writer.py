# writer.py

import json
import logging
import threading
import time
from clickhouse_driver import Client
from prometheus_client import Counter, Gauge

db_insert = Counter('metric_rtr_db_inserts', 'Database inserts')
db_insert_fail = Counter('metric_rtr_db_insert_fail', 'Failed Database inserts')
flush_on_size = Counter('metric_rtr_flush_on_size', 'Flush on bucket size')
flush_on_time = Counter('metric_rtr_flush_on_time', 'Flush on bucket time')
measurements_pruned = Counter('metric_rtr_measurements_pruned', 'Pruned stale measurements')
metric_insert_size = Gauge('metric_rtr_insert_size', 'Row count of db insert')

logger = logging.getLogger()

list_lock = threading.Lock()

def flush_to_db(ch_client, metric_bucket):

    list_lock.acquire()

    columns = []
    
    for j in metric_bucket.metrics:
        columns.append({**j['tags'], **j['fields'], 'ts': int(j['time'].to_unix())})
    json_cols = json.dumps(columns)
    sql_cmd = f'INSERT INTO {metric_bucket.name} FORMAT JSONEachRow {json_cols}'
    try:
        ch_client.execute(sql_cmd)  
        db_insert.inc()
    except:
        db_insert_fail.inc()

    metric_insert_size.set(len(metric_bucket.metrics))
    metric_bucket.metrics.clear()
    metric_bucket.update_time = time.time()

    list_lock.release()
    

def metric_writer(metric_bucket, args, config):

    ch_client = Client(
            host = config['writer'].get('db_server'), 
            port = config['writer'].get('db_server_port')
            )

    while True:

        for k in metric_bucket.keys():

            measurement_last_update = time.time() - metric_bucket[k].update_time
            measurement_bucket_size = len(metric_bucket[k].metrics)  

            logger.debug(f'Processing {k} update time:{measurement_last_update} len:{measurement_bucket_size}')
            '''
            If more than 100 metrics -> dump to database
            If 1 or more metrics and last update time gt 60 seconds -> dump to database
            If empty bucket and bucket older than 300 sec -> delete bucket 
            '''

            max_bucket_size = config['writer'].get('max_bucket_size')
            bucket_time_trigger = config['writer'].get('bucket_time_trigger')
            max_bucket_age = config['writer'].get('max_bucket_age')

            if measurement_bucket_size > max_bucket_size:
                flush_to_db(ch_client, metric_bucket[k])
                flush_on_size.inc()
            elif measurement_last_update > bucket_time_trigger and measurement_bucket_size > 0:
                flush_to_db(ch_client, metric_bucket[k])
                flush_on_time.inc()
            elif measurement_last_update > max_bucket_age and measurement_bucket_size == 0:
                del metric_bucket[k]
                measurements_pruned.inc()

        time.sleep(config['writer'].get('writer_sleep'))