"""Tests for logslice.contexter and logslice.context_reporter."""
from __future__ import annotations

import json
import pytest

from logslice.contexter import ContextResult, extract_context
from logslice.context_reporter import (
    get_context_reporter,
    report_context_json,
    report_context_text,
)

LOG_LINES = [
    "2024-01-01 00:00:01 DEBUG  starting up",
    "2024-01-01 00:00:02 INFO   connected",
    "2024-01-01 00:00:03 ERROR  disk full",
    "2024-01-01 00:00:04 INFO   retrying",
    "2024-01-01 00:00:05 DEBUG  loop tick",
    "2024-01-01 00:00:06 ERROR  timeout",
    "2024-01-01 00:00:07 INFO   recovered",
    "2024-01-01 00:00:08 DEBUG  shutting down",
]


def test_extract_context_returns_context_result():
    result = extract_context(LOG_LINES, "ERROR")
    assert isinstance(result, ContextResult)


def test_extract_context_match_count():
    result = extract_context(LOG_LINES, "ERROR")
    assert result.match_count == 2


def test_extract_context_total_input():
    result = extract_context(LOG_LINES, "ERROR")
    assert result.total_input == len(LOG_LINES)


def test_extract_context_includes_surrounding_lines():
    # Match at index 2 (line 3): before=1 → line 2, after=1 → line 4
    result = extract_context(LOG_LINES, "disk full", before=1, after=1)
    line_numbers = [ln for ln, _ in result.lines]
    assert 2 in line_numbers  # before
    assert 3 in line_numbers  # match
    assert 4 in line_numbers  # after


def test_extract_context_no_match_returns_empty():
    result = extract_context(LOG_LINES, "CRITICAL")
    assert result.match_count == 0
    assert result.lines == []


def test_extract_context_case_insensitive_default():
    result = extract_context(LOG_LINES, "error", before=0, after=0)
    assert result.match_count == 2


def test_extract_context_case_sensitive_no_match():
    result = extract_context(LOG_LINES, "error", before=0, after=0, case_sensitive=True)
    assert result.match_count == 0


def test_extract_context_overlapping_windows_deduplicated():
    # Two ERRORs at indices 2 and 5 with before=2, after=2 — windows overlap.
    result = extract_context(LOG_LINES, "ERROR", before=2, after=2)
    line_numbers = [ln for ln, _ in result.lines]
    assert len(line_numbers) == len(set(line_numbers)), "duplicate line numbers in output"


def test_extract_context_negative_before_raises():
    with pytest.raises(ValueError):
        extract_context(LOG_LINES, "ERROR", before=-1)


def test_extract_context_negative_after_raises():
    with pytest.raises(ValueError):
        extract_context(LOG_LINES, "ERROR", after=-1)


def test_report_context_text_returns_string():
    result = extract_context(LOG_LINES, "ERROR")
    text = report_context_text(result)
    assert isinstance(text, str)


def test_report_context_text_contains_match_count():
    result = extract_context(LOG_LINES, "ERROR")
    text = report_context_text(result)
    assert "2" in text


def test_report_context_json_is_valid_json():
    result = extract_context(LOG_LINES, "ERROR")
    raw = report_context_json(result)
    parsed = json.loads(raw)
    assert "match_count" in parsed
    assert "lines" in parsed


def test_report_context_json_lines_have_lineno_and_text():
    result = extract_context(LOG_LINES, "disk full", before=0, after=0)
    parsed = json.loads(report_context_json(result))
    assert len(parsed["lines"]) == 1
    assert "lineno" in parsed["lines"][0]
    assert "text" in parsed["lines"][0]


def test_get_context_reporter_text():
    fn = get_context_reporter("text")
    result = extract_context(LOG_LINES, "ERROR")
    assert isinstance(fn(result), str)


def test_get_context_reporter_json():
    fn = get_context_reporter("json")
    result = extract_context(LOG_LINES, "ERROR")
    json.loads(fn(result))  # should not raise


def test_get_context_reporter_unknown_raises():
    with pytest.raises(ValueError):
        get_context_reporter("xml")
