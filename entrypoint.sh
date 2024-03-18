#!/usr/bin/env bash

sleep 5
python3 /app/metric-router.py -c /app/config.toml $@
