#!/bin/bash

set -e

clickhouse-client -mn << ESQL

    CREATE TABLE IF NOT EXISTS system (
        -- ts datetime('America/New_York'),
        ts UInt64,
        host String,
        load1 Float32,
        load5 Float32,
        load15 Float32,
        n_cpus UInt16
    ) ENGINE MergeTree ORDER BY ts;

ESQL