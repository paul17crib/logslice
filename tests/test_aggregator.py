"""Tests for logslice.aggregator."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from logslice.aggregator import AggregateResult, AggregateWindow, aggregate


def _line(ts: str, msg: str = "log message") -> str:
    return f"{ts} {msg}"


LINES_60S = [
    _line("2024-01-01T00:00:05Z", "alpha"),
    _line("2024-01-01T00:00:30Z", "beta"),
    _line("2024-01-01T00:01:10Z", "gamma"),
    _line("2024-01-01T00:02:05Z", "delta"),
    _line("2024-01-01T00:02:45Z", "epsilon"),
]


def test_aggregate_returns_aggregate_result():
    result = aggregate(LINES_60S)
    assert isinstance(result, AggregateResult)


def test_aggregate_windows_are_aggregate_window_instances():
    result = aggregate(LINES_60S)
    for w in result.windows:
        assert isinstance(w, AggregateWindow)


def test_aggregate_total_lines_matches_input():
    result = aggregate(LINES_60S)
    assert result.total_lines == len(LINES_60S)


def test_aggregate_correct_window_count():
    # 00:00, 00:01, 00:02 → 3 windows
    result = aggregate(LINES_60S, window_seconds=60)
    assert result.window_count == 3


def test_aggregate_window_counts_sum_to_timestamped_lines():
    result = aggregate(LINES_60S, window_seconds=60)
    assert sum(w.count for w in result.windows) == result.total_lines - result.ungrouped


def test_aggregate_ungrouped_zero_when_all_have_timestamps():
    result = aggregate(LINES_60S)
    assert result.ungrouped == 0


def test_aggregate_ungrouped_counts_lines_without_timestamp():
    lines = LINES_60S + ["no timestamp here", "another bare line"]
    result = aggregate(lines)
    assert result.ungrouped == 2


def test_aggregate_window_seconds_stored():
    result = aggregate(LINES_60S, window_seconds=30)
    assert result.window_seconds == 30


def test_aggregate_peak_window_has_highest_count():
    result = aggregate(LINES_60S, window_seconds=60)
    peak = result.peak_window
    assert peak is not None
    assert peak.count == max(w.count for w in result.windows)


def test_aggregate_peak_window_none_when_no_windows():
    result = aggregate([], window_seconds=60)
    assert result.peak_window is None


def test_aggregate_windows_sorted_chronologically():
    result = aggregate(LINES_60S, window_seconds=60)
    starts = [w.start for w in result.windows]
    assert starts == sorted(starts)


def test_aggregate_max_samples_limits_stored_lines():
    many = [_line("2024-01-01T00:00:01Z", f"msg{i}") for i in range(20)]
    result = aggregate(many, window_seconds=60, max_samples=3)
    for w in result.windows:
        assert len(w.lines) <= 3


def test_aggregate_invalid_window_seconds_raises():
    with pytest.raises(ValueError):
        aggregate(LINES_60S, window_seconds=0)


def test_aggregate_empty_input():
    result = aggregate([])
    assert result.total_lines == 0
    assert result.window_count == 0
    assert result.ungrouped == 0


def test_aggregate_window_label_format():
    result = aggregate([_line("2024-06-15T12:34:00Z")], window_seconds=60)
    assert result.windows[0].label == "2024-06-15T12:34:00"
