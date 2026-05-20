"""Tests for logslice.stats and logslice.reporter."""

from __future__ import annotations

import io
import json
from datetime import datetime, timezone

import pytest

from logslice.stats import SliceStats, collect_stats
from logslice.reporter import get_reporter, report_json, report_text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TS_A = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
TS_B = datetime(2024, 1, 15, 10, 0, 30, tzinfo=timezone.utc)

LINES = [
    "2024-01-15T10:00:00Z INFO  server started",
    "    stack trace line 1",
    "    stack trace line 2",
    "2024-01-15T10:00:30Z ERROR something broke",
]


def _parse_ts(line: str):
    """Minimal parser used in tests."""
    try:
        ts_str = line.split(" ")[0]
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except (ValueError, IndexError):
        return None


# ---------------------------------------------------------------------------
# SliceStats
# ---------------------------------------------------------------------------

def test_duration_seconds_none_when_no_timestamps():
    stats = SliceStats()
    assert stats.duration_seconds is None


def test_duration_seconds_calculated():
    stats = SliceStats(first_timestamp=TS_A, last_timestamp=TS_B)
    assert stats.duration_seconds == pytest.approx(30.0)


def test_to_dict_keys():
    stats = SliceStats(total_lines=10, matched_lines=8)
    d = stats.to_dict()
    assert set(d.keys()) == {
        "total_lines", "matched_lines", "continuation_lines",
        "skipped_lines", "first_timestamp", "last_timestamp", "duration_seconds",
    }


# ---------------------------------------------------------------------------
# collect_stats
# ---------------------------------------------------------------------------

def test_collect_stats_counts():
    collected, stats = collect_stats(iter(LINES), _parse_ts)
    assert stats.total_lines == 4
    assert stats.matched_lines == 2
    assert stats.continuation_lines == 2
    assert collected == LINES


def test_collect_stats_timestamps():
    _, stats = collect_stats(iter(LINES), _parse_ts)
    assert stats.first_timestamp == TS_A
    assert stats.last_timestamp == TS_B


def test_collect_stats_empty():
    collected, stats = collect_stats(iter([]), _parse_ts)
    assert collected == []
    assert stats.total_lines == 0
    assert stats.duration_seconds is None


# ---------------------------------------------------------------------------
# Reporter
# ---------------------------------------------------------------------------

def test_report_text_writes_to_file():
    stats = SliceStats(total_lines=5, matched_lines=3, first_timestamp=TS_A, last_timestamp=TS_B)
    buf = io.StringIO()
    report_text(stats, file=buf)
    output = buf.getvalue()
    assert "Total lines" in output
    assert "5" in output
    assert "30.000s" in output


def test_report_json_valid_json():
    stats = SliceStats(total_lines=2, matched_lines=2)
    buf = io.StringIO()
    report_json(stats, file=buf)
    data = json.loads(buf.getvalue())
    assert data["total_lines"] == 2


def test_get_reporter_unknown_raises():
    with pytest.raises(ValueError, match="Unknown report format"):
        get_reporter("xml")  # type: ignore[arg-type]


def test_get_reporter_returns_callables():
    assert get_reporter("text") is report_text
    assert get_reporter("json") is report_json
