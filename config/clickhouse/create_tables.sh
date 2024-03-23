#!/bin/bash

set -e

clickhouse-client -mn << ESQL

    CREATE TABLE IF NOT EXISTS diskio (
        ts UInt64,
        host LowCardinality(String),
        name LowCardinality(String),
        serial LowCardinality(String),
        reads UInt64,
        writes UInt64,
        read_bytes UInt64,
        write_bytes UInt64,
        io_time UInt64,
        weighted_io_time UInt64,
        iops_in_progress UInt64,
        merged_reads UInt64,
        merged_writes UInt64
    ) ENGINE MergeTree ORDER BY ts;

    CREATE TABLE IF NOT EXISTS system (
        ts UInt64,
        host LowCardinality(String),
        load1 Float32,
        load5 Float32,
        load15 Float32,
        n_cpus UInt16
    ) ENGINE MergeTree ORDER BY ts;

    CREATE TABLE IF NOT EXISTS swap (
        ts UInt64,
        host LowCardinality(String),
        free UInt64,
        total UInt64,
        used UInt64,
        used_percent Float32,
        in UInt64,
        out UInt64
    ) ENGINE MergeTree ORDER BY ts;

ESQL