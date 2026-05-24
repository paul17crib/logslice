"""Tests for logslice.summarizer."""
import pytest
from logslice.summarizer import SummaryResult, summarize


SAMPLE_LINES = [
    "2024-01-01 10:00:00 INFO  Service started",
    "2024-01-01 10:00:01 DEBUG Checking config",
    "2024-01-01 10:00:02 WARNING Disk usage high",
    "2024-01-01 10:00:03 ERROR  Connection refused",
    "2024-01-01 10:00:04 ERROR  Connection refused",
    "2024-01-01 10:00:05 CRITICAL Out of memory",
    "    continuation line for above",
    "2024-01-01 10:00:06 INFO  Shutting down",
]


def test_summarize_returns_summary_result():
    result = summarize(SAMPLE_LINES)
    assert isinstance(result, SummaryResult)


def test_summarize_total_lines():
    result = summarize(SAMPLE_LINES)
    assert result.total_lines == len(SAMPLE_LINES)


def test_summarize_severity_counts_has_error():
    result = summarize(SAMPLE_LINES)
    assert result.severity_counts.get("ERROR", 0) >= 2


def test_summarize_top_errors_limited_by_top_n():
    result = summarize(SAMPLE_LINES, top_n=1)
    assert len(result.top_errors) <= 1


def test_summarize_top_errors_most_frequent_first():
    result = summarize(SAMPLE_LINES, top_n=5)
    # "Connection refused" appears twice, should be first
    if result.top_errors:
        assert "Connection refused" in result.top_errors[0]


def test_summarize_unique_line_count_lte_total():
    result = summarize(SAMPLE_LINES)
    assert result.unique_line_count <= result.total_lines


def test_summarize_unique_line_count_reflects_duplicates():
    lines = ["2024-01-01 10:00:00 ERROR same"] * 4
    result = summarize(lines)
    assert result.unique_line_count == 1


def test_summarize_empty_input():
    result = summarize([])
    assert result.total_lines == 0
    assert result.top_errors == []
    assert result.unique_line_count == 0


def test_summarize_custom_error_severities():
    lines = [
        "2024-01-01 10:00:00 WARNING watch out",
        "2024-01-01 10:00:01 INFO   all fine",
    ]
    result = summarize(lines, error_severities=("WARNING",))
    assert len(result.top_errors) >= 1


def test_summarize_top_errors_default_empty_when_no_errors():
    lines = [
        "2024-01-01 10:00:00 INFO  all good",
        "2024-01-01 10:00:01 DEBUG details",
    ]
    result = summarize(lines)
    assert result.top_errors == []
