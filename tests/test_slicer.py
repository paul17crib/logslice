"""Unit tests for logslice.slicer core slicing functionality."""

import os
import tempfile
from datetime import datetime

import pytest

from logslice.slicer import slice_log, count_lines

SAMPLE_LOG = """2024-01-15 10:00:00 INFO  application starting
2024-01-15 10:01:00 DEBUG loading config
    config path: /etc/app/config.yaml
2024-01-15 10:02:00 INFO  server listening on :8080
2024-01-15 10:03:00 WARN  high memory usage detected
2024-01-15 10:04:00 ERROR connection refused
    retrying in 5s
2024-01-15 10:05:00 INFO  connection restored
"""


@pytest.fixture
def log_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(SAMPLE_LOG)
        path = f.name
    yield path
    os.unlink(path)


def test_slice_full_range(log_file):
    start = datetime(2024, 1, 15, 10, 0, 0)
    end = datetime(2024, 1, 15, 10, 5, 0)
    lines = list(slice_log(log_file, start, end))
    assert len(lines) == 8  # 6 timestamped + 2 continuation


def test_slice_partial_range(log_file):
    start = datetime(2024, 1, 15, 10, 2, 0)
    end = datetime(2024, 1, 15, 10, 3, 0)
    lines = list(slice_log(log_file, start, end))
    assert any('server listening' in l for l in lines)
    assert any('high memory' in l for l in lines)
    assert not any('loading config' in l for l in lines)


def test_slice_continuation_lines_included(log_file):
    start = datetime(2024, 1, 15, 10, 4, 0)
    end = datetime(2024, 1, 15, 10, 4, 0)
    lines = list(slice_log(log_file, start, end))
    assert any('connection refused' in l for l in lines)
    assert any('retrying in 5s' in l for l in lines)


def test_slice_empty_range(log_file):
    start = datetime(2024, 1, 15, 11, 0, 0)
    end = datetime(2024, 1, 15, 12, 0, 0)
    lines = list(slice_log(log_file, start, end))
    assert lines == []


def test_slice_invalid_range(log_file):
    with pytest.raises(ValueError):
        list(slice_log(log_file, datetime(2024, 1, 15, 10, 5, 0), datetime(2024, 1, 15, 10, 0, 0)))


def test_slice_missing_file():
    with pytest.raises(FileNotFoundError):
        list(slice_log('/nonexistent/path/app.log', datetime.now(), datetime.now()))


def test_count_lines(log_file):
    start = datetime(2024, 1, 15, 10, 0, 0)
    end = datetime(2024, 1, 15, 10, 5, 0)
    count, first_ts, last_ts = count_lines(log_file, start, end)
    assert count == 8
    assert first_ts == datetime(2024, 1, 15, 10, 0, 0)
    assert last_ts == datetime(2024, 1, 15, 10, 5, 0)
