#!/usr/bin/env python3

import argparse
import asyncio
import logging
import threading
import toml
from consumer import metric_consumer
from classifier import metric_classifier
from writer import metric_writer
from prometheus_client import start_http_server


def cli_args():

    parser = argparse.ArgumentParser(description='Metric Router')
    parser.add_argument('-v', dest='verbose', action='store_true')
    parser.add_argument('-c', dest='cfg_file', action='store', default='/app/config.toml')
    return parser.parse_args()


def get_logger(args):

    logger = logging.getLogger()
    if args.verbose:
        logging.basicConfig(format='%(levelname)s - %(message)s',level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s - %(message)s',level=logging.WARNING)
    return logger


def read_config(fn):

    with open(fn) as fh:
        toml_data = toml.load(fh)
    return toml_data


async def main(args, config):

    msg_queue = asyncio.Queue()
    metric_bucket = {}

    # Start threaded task
    writer_task = threading.Thread(target=metric_writer, args=(metric_bucket, args, config))
    writer_task.start()

    # Start async tasks
    consumer_task = asyncio.create_task(metric_consumer(msg_queue, config))
    classifier_task = asyncio.create_task(metric_classifier(msg_queue, metric_bucket))
    await asyncio.gather(consumer_task, classifier_task)


if __name__ == '__main__':
    
    args = cli_args()
    config = read_config(args.cfg_file)
    logger = get_logger(args)
    start_http_server(8000)

    asyncio.run(main(args, config))