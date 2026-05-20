"""Tests for logslice.formatter."""

from __future__ import annotations

import json
from datetime import datetime

import pytest

from logslice.formatter import (
    format_json_stream,
    format_numbered,
    format_plain,
    get_formatter,
)

SAMPLE_LINES = ["alpha\n", "beta\n", "gamma\n"]


def test_format_plain_passthrough():
    result = list(format_plain(SAMPLE_LINES))
    assert result == SAMPLE_LINES


def test_format_plain_empty():
    assert list(format_plain([])) == []


def test_format_numbered_prefixes():
    result = list(format_numbered(SAMPLE_LINES))
    assert len(result) == 3
    assert result[0].strip().startswith("1")
    assert "alpha" in result[0]


def test_format_numbered_custom_start():
    result = list(format_numbered(SAMPLE_LINES, start=10))
    assert result[0].strip().startswith("10")
    assert result[2].strip().startswith("12")


def test_format_json_stream_structure():
    output = list(format_json_stream(SAMPLE_LINES))
    # header + 3 lines + footer
    assert len(output) == 5

    header = json.loads(output[0])
    assert header["type"] == "header"

    for raw in output[1:4]:
        record = json.loads(raw)
        assert record["type"] == "line"
        assert "n" in record
        assert "text" in record

    footer = json.loads(output[-1])
    assert footer["type"] == "footer"
    assert footer["total_lines"] == 3


def test_format_json_stream_timestamps():
    start = datetime(2024, 1, 1, 0, 0, 0)
    end = datetime(2024, 1, 1, 1, 0, 0)
    output = list(format_json_stream(SAMPLE_LINES, start_time=start, end_time=end))
    header = json.loads(output[0])
    assert header["start_time"] == start.isoformat()
    assert header["end_time"] == end.isoformat()


def test_format_json_stream_empty():
    output = list(format_json_stream([]))
    footer = json.loads(output[-1])
    assert footer["total_lines"] == 0


def test_get_formatter_valid():
    for name in ("plain", "numbered", "json"):
        fn = get_formatter(name)
        assert callable(fn)


def test_get_formatter_invalid():
    with pytest.raises(ValueError, match="Unknown format"):
        get_formatter("xml")
