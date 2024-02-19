#!/usr/bin/env python3

import argparse
import asyncio
import logging
from consumer import metric_consumer
from publisher import metric_writer
from prometheus_client import start_http_server

def cli_args():
    parser = argparse.ArgumentParser(description='Metric Router')
    parser.add_argument('-v', dest='verbose', action='store_true')
    parser.add_argument('-c', dest='ch_host', action='store', default='clickhouse')
    parser.add_argument('-b', dest='bootstrap_server', action='store', default='redpanda:9092')
    parser.add_argument('-t', dest='kafka_topic', action='store', default='telegraf')
    parser.add_argument('-g', dest='group_id', action='store', default='metrics')
    return parser.parse_args()

def get_logger(args):
    logger = logging.getLogger()
    if args.verbose:
        logging.basicConfig(format='%(levelname)s - %(message)s',level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s - %(message)s',level=logging.WARNING)
    return logger

async def main(args):

    msg_queue = asyncio.Queue()

    kafka_task = asyncio.create_task(metric_consumer(msg_queue, args))
    db_task = asyncio.create_task(metric_writer(msg_queue, args))
    
    await asyncio.gather(kafka_task, db_task)

if __name__ == '__main__':
    
    args = cli_args()
    logger = get_logger(args)
    start_http_server(8000)

    asyncio.run(main(args))
