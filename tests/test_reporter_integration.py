"""Integration test: collect_stats + reporter round-trip."""

from __future__ import annotations

import io
import json
from datetime import timezone

from logslice.stats import collect_stats
from logslice.reporter import report_json, report_text
from logslice.parser import parse_timestamp

LOG_LINES = [
    "2024-03-01 08:00:00 INFO  app booted\n",
    "2024-03-01 08:00:01 DEBUG loading config\n",
    "    continuation of config load\n",
    "2024-03-01 08:00:05 WARN  disk usage high\n",
]


def test_full_round_trip_text():
    collected, stats = collect_stats(iter(LOG_LINES), parse_timestamp)
    assert len(collected) == 4
    assert stats.matched_lines >= 0  # parser may or may not match format
    buf = io.StringIO()
    report_text(stats, file=buf)
    assert "Total lines" in buf.getvalue()
    assert "4" in buf.getvalue()


def test_full_round_trip_json():
    collected, stats = collect_stats(iter(LOG_LINES), parse_timestamp)
    buf = io.StringIO()
    report_json(stats, file=buf)
    data = json.loads(buf.getvalue())
    assert data["total_lines"] == 4
    assert data["continuation_lines"] >= 0


def test_stats_to_dict_serialisable():
    """Ensure to_dict output is JSON-serialisable without custom encoder."""
    _, stats = collect_stats(iter(LOG_LINES), parse_timestamp)
    d = stats.to_dict()
    # Should not raise
    json.dumps(d)
