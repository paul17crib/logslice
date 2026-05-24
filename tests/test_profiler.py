"""Tests for logslice.profiler and logslice.profile_reporter."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from logslice.profiler import GapInfo, ProfileResult, profile
from logslice.profile_reporter import (
    get_profile_reporter,
    report_profile_json,
    report_profile_text,
)


LOG_LINES = [
    "2024-01-01T00:00:00 INFO  starting up",
    "2024-01-01T00:00:01 DEBUG loop tick",
    "continuation line with no timestamp",
    "2024-01-01T00:00:02 INFO  tick 2",
    "2024-01-01T00:05:00 WARN  long pause here",  # ~5-min gap
    "2024-01-01T00:05:01 INFO  resumed",
]


def test_profile_returns_profile_result():
    result = profile(LOG_LINES)
    assert isinstance(result, ProfileResult)


def test_profile_total_lines():
    result = profile(LOG_LINES)
    assert result.total_lines == len(LOG_LINES)


def test_profile_timestamped_lines():
    result = profile(LOG_LINES)
    assert result.timestamped_lines == 5


def test_profile_coverage_ratio():
    result = profile(LOG_LINES)
    assert abs(result.coverage_ratio - 5 / 6) < 1e-9


def test_profile_first_and_last_timestamp():
    result = profile(LOG_LINES)
    assert result.first_timestamp is not None
    assert result.last_timestamp is not None
    assert result.first_timestamp < result.last_timestamp


def test_profile_duration_seconds():
    result = profile(LOG_LINES)
    assert result.duration_seconds is not None
    assert result.duration_seconds == pytest.approx(301.0, abs=1.0)


def test_profile_lines_per_second():
    result = profile(LOG_LINES)
    assert result.lines_per_second is not None
    assert result.lines_per_second > 0


def test_profile_detects_gap():
    result = profile(LOG_LINES, gap_threshold_seconds=60.0)
    assert len(result.gaps) == 1
    assert isinstance(result.gaps[0], GapInfo)
    assert result.gaps[0].duration_seconds == pytest.approx(298.0, abs=1.0)


def test_profile_no_gap_below_threshold():
    result = profile(LOG_LINES, gap_threshold_seconds=600.0)
    assert result.gaps == []


def test_profile_empty_input():
    result = profile([])
    assert result.total_lines == 0
    assert result.timestamped_lines == 0
    assert result.first_timestamp is None
    assert result.duration_seconds is None
    assert result.coverage_ratio == 0.0


def test_profile_no_timestamps():
    result = profile(["no ts here", "also no ts"])
    assert result.timestamped_lines == 0
    assert result.lines_per_second is None


# --- reporter tests ---


def test_report_text_returns_string():
    result = profile(LOG_LINES)
    assert isinstance(report_profile_text(result), str)


def test_report_text_contains_total_lines():
    result = profile(LOG_LINES)
    text = report_profile_text(result)
    assert str(result.total_lines) in text


def test_report_text_contains_gap_info():
    result = profile(LOG_LINES, gap_threshold_seconds=60.0)
    text = report_profile_text(result)
    assert "Gap 1" in text


def test_report_json_is_valid_json():
    result = profile(LOG_LINES)
    data = json.loads(report_profile_json(result))
    assert "total_lines" in data
    assert "gaps" in data


def test_report_json_gap_count_matches():
    result = profile(LOG_LINES, gap_threshold_seconds=60.0)
    data = json.loads(report_profile_json(result))
    assert len(data["gaps"]) == len(result.gaps)


def test_get_profile_reporter_text():
    reporter = get_profile_reporter("text")
    assert reporter is report_profile_text


def test_get_profile_reporter_json():
    reporter = get_profile_reporter("json")
    assert reporter is report_profile_json


def test_get_profile_reporter_invalid():
    with pytest.raises(ValueError):
        get_profile_reporter("xml")
