"""Unit tests for logslice.parser timestamp detection."""

import pytest
from datetime import datetime
from logslice.parser import parse_timestamp


@pytest.mark.parametrize("line, expected", [
    # ISO 8601 with fractional seconds and Z
    (
        "2024-01-15T13:45:00.123Z INFO service started",
        datetime(2024, 1, 15, 13, 45, 0),
    ),
    # ISO 8601 without fractional seconds
    (
        "2024-01-15T13:45:00 ERROR something failed",
        datetime(2024, 1, 15, 13, 45, 0),
    ),
    # Common log format with comma-separated millis
    (
        "2024-01-15 13:45:00,456 DEBUG processing request",
        datetime(2024, 1, 15, 13, 45, 0),
    ),
    # Common log format with dot-separated millis
    (
        "2024-01-15 13:45:00.789 WARN high memory",
        datetime(2024, 1, 15, 13, 45, 0),
    ),
    # Common log format without millis
    (
        "2024-01-15 13:45:00 INFO plain timestamp",
        datetime(2024, 1, 15, 13, 45, 0),
    ),
    # Apache/nginx style
    (
        '192.168.1.1 - - [15/Jan/2024:13:45:00 +0000] "GET / HTTP/1.1" 200',
        datetime(2024, 1, 15, 13, 45, 0),
    ),
    # No timestamp
    (
        "    at com.example.App.main(App.java:42)",
        None,
    ),
    # Empty line
    (
        "",
        None,
    ),
])
def test_parse_timestamp(line, expected):
    result = parse_timestamp(line)
    if expected is None:
        assert result is None
    else:
        assert result is not None
        assert result.year == expected.year
        assert result.month == expected.month
        assert result.day == expected.day
        assert result.hour == expected.hour
        assert result.minute == expected.minute
        assert result.second == expected.second


def test_parse_timestamp_returns_datetime_instance():
    line = "2024-06-01 00:00:00 boot complete"
    result = parse_timestamp(line)
    assert isinstance(result, datetime)
