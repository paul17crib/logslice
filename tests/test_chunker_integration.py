"""Integration tests: chunker + chunk_reporter round-trip."""
from __future__ import annotations

import json
from datetime import timedelta

from logslice.chunker import chunk
from logslice.chunk_reporter import report_chunk_json, report_chunk_text


TIMESTAMPED = [
    "2024-06-01T10:00:00 INFO  service started",
    "2024-06-01T10:00:30 DEBUG heartbeat",
    "2024-06-01T10:01:05 WARN  high memory",
    "2024-06-01T10:01:45 ERROR disk full",
    "2024-06-01T10:02:10 INFO  recovered",
    "2024-06-01T10:02:55 INFO  shutdown",
]


def test_size_chunk_text_round_trip_line_count():
    result = chunk(TIMESTAMPED, chunk_size=3)
    text = report_chunk_text(result)
    assert str(len(TIMESTAMPED)) in text


def test_time_chunk_json_round_trip_total_lines():
    result = chunk(TIMESTAMPED, window=timedelta(minutes=1))
    data = json.loads(report_chunk_json(result))
    assert data["total_lines"] == len(TIMESTAMPED)


def test_time_chunk_json_chunk_lines_reconstruct_input():
    result = chunk(TIMESTAMPED, window=timedelta(minutes=1))
    data = json.loads(report_chunk_json(result))
    reconstructed = [line for c in data["chunks"] for line in c["lines"]]
    assert reconstructed == TIMESTAMPED


def test_size_chunk_json_chunk_sizes_sum_to_total():
    result = chunk(TIMESTAMPED, chunk_size=2)
    data = json.loads(report_chunk_json(result))
    assert sum(c["size"] for c in data["chunks"]) == data["total_lines"]


def test_chunk_count_matches_reporter_output():
    result = chunk(TIMESTAMPED, chunk_size=2)
    data = json.loads(report_chunk_json(result))
    assert data["chunk_count"] == result.chunk_count
