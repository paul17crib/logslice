"""Tests for logslice.diff_reporter."""
import json
import pytest

from logslice.differ import diff_logs
from logslice.diff_reporter import (
    get_diff_reporter,
    report_diff_json,
    report_diff_text,
)


LINES_A = ["2024-01-01 INFO start", "2024-01-01 DEBUG loop", "2024-01-01 INFO end"]
LINES_B = ["2024-01-01 INFO start", "2024-01-01 WARNING changed", "2024-01-01 INFO end"]


def _result():
    return diff_logs(LINES_A, LINES_B)


def test_report_text_returns_string():
    assert isinstance(report_diff_text(_result()), str)


def test_report_text_contains_header():
    text = report_diff_text(_result())
    assert "--- a" in text


def test_report_text_contains_removed_marker():
    text = report_diff_text(_result())
    assert "- " in text


def test_report_text_contains_added_marker():
    text = report_diff_text(_result())
    assert "+ " in text


def test_report_text_change_ratio_present():
    text = report_diff_text(_result())
    assert "change_ratio" in text


def test_report_json_returns_string():
    assert isinstance(report_diff_json(_result()), str)


def test_report_json_is_valid_json():
    payload = json.loads(report_diff_json(_result()))
    assert isinstance(payload, dict)


def test_report_json_has_required_keys():
    payload = json.loads(report_diff_json(_result()))
    for key in ("added", "removed", "equal", "total", "change_ratio", "lines"):
        assert key in payload


def test_report_json_lines_is_list():
    payload = json.loads(report_diff_json(_result()))
    assert isinstance(payload["lines"], list)


def test_report_json_counts_consistent():
    result = _result()
    payload = json.loads(report_diff_json(result))
    assert payload["added"] == result.added
    assert payload["removed"] == result.removed
    assert payload["equal"] == result.equal


def test_get_diff_reporter_text():
    fn = get_diff_reporter("text")
    assert fn is report_diff_text


def test_get_diff_reporter_json():
    fn = get_diff_reporter("json")
    assert fn is report_diff_json


def test_get_diff_reporter_invalid_raises():
    with pytest.raises(ValueError):
        get_diff_reporter("xml")
