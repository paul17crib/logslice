"""Integration tests: classifier + filter_by_severity working together."""

from logslice.classifier import classify
from logslice.filter_by_severity import filter_by_severity


LOG_LINES = [
    "2024-03-01T10:00:00 DEBUG polling heartbeat",
    "2024-03-01T10:00:01 INFO  request received path=/health",
    "2024-03-01T10:00:02 WARNING retry attempt 2/3",
    "2024-03-01T10:00:03 ERROR  upstream timeout after 30s",
    "2024-03-01T10:00:04 CRITICAL fatal oom-killer invoked",
    "    at com.example.App.main(App.java:42)",  # continuation / unclassified
]


def test_classify_then_filter_errors_and_above():
    result = filter_by_severity(LOG_LINES, min_level="ERROR", include_unclassified=False)
    assert result.kept == 2
    assert any("ERROR" in l for l in result.lines)
    assert any("CRITICAL" in l for l in result.lines)


def test_classify_severity_counts_match_filter_kept():
    classify_result = classify(LOG_LINES)
    counts = classify_result.counts_by_severity()
    filter_result = filter_by_severity(LOG_LINES, min_level="WARNING", include_unclassified=False)
    expected = counts["WARNING"] + counts["ERROR"] + counts["CRITICAL"]
    assert filter_result.kept == expected


def test_filter_debug_only():
    result = filter_by_severity(LOG_LINES, min_level="DEBUG", max_level="DEBUG", include_unclassified=False)
    assert result.kept == 1
    assert "DEBUG" in result.lines[0]


def test_unclassified_continuation_lines_passthrough():
    result = filter_by_severity(LOG_LINES, min_level="ERROR", include_unclassified=True)
    continuation = [l for l in result.lines if l.startswith("    at ")]
    assert len(continuation) == 1


def test_full_pipeline_no_lines_lost_with_no_bounds():
    classify_result = classify(LOG_LINES)
    filter_result = filter_by_severity(LOG_LINES, include_unclassified=True)
    assert filter_result.kept == classify_result.total
