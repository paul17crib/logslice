"""Tests for logslice.summary_reporter."""
import json
import pytest
from logslice.summarizer import SummaryResult
from logslice.summary_reporter import (
    get_summary_reporter,
    report_summary_json,
    report_summary_text,
)


def _make_result(**kwargs) -> SummaryResult:
    defaults = dict(
        total_lines=10,
        first_timestamp="2024-01-01 10:00:00",
        last_timestamp="2024-01-01 10:00:09",
        severity_counts={"INFO": 5, "ERROR": 3, "DEBUG": 2},
        top_errors=["Connection refused", "Timeout"],
        unique_line_count=8,
    )
    defaults.update(kwargs)
    return SummaryResult(**defaults)


def test_report_text_returns_string():
    assert isinstance(report_summary_text(_make_result()), str)


def test_report_text_contains_total_lines():
    text = report_summary_text(_make_result(total_lines=42))
    assert "42" in text


def test_report_text_contains_severity():
    text = report_summary_text(_make_result())
    assert "ERROR" in text


def test_report_text_contains_top_error():
    text = report_summary_text(_make_result())
    assert "Connection refused" in text


def test_report_text_no_top_errors_section_when_empty():
    text = report_summary_text(_make_result(top_errors=[]))
    assert "Top errors" not in text


def test_report_json_returns_valid_json():
    raw = report_summary_json(_make_result())
    parsed = json.loads(raw)
    assert isinstance(parsed, dict)


def test_report_json_has_expected_keys():
    parsed = json.loads(report_summary_json(_make_result()))
    for key in ("total_lines", "unique_line_count", "severity_counts", "top_errors"):
        assert key in parsed


def test_report_json_top_errors_is_list():
    parsed = json.loads(report_summary_json(_make_result()))
    assert isinstance(parsed["top_errors"], list)


def test_get_summary_reporter_text():
    fn = get_summary_reporter("text")
    assert callable(fn)
    assert "42" in fn(_make_result(total_lines=42))


def test_get_summary_reporter_json():
    fn = get_summary_reporter("json")
    result = json.loads(fn(_make_result()))
    assert "total_lines" in result


def test_get_summary_reporter_invalid_raises():
    with pytest.raises(ValueError, match="Unknown summary format"):
        get_summary_reporter("xml")
