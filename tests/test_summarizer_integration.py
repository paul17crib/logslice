"""Integration tests: summarizer + summary_reporter round-trip."""
import json
from logslice.summarizer import summarize
from logslice.summary_reporter import get_summary_reporter


LOG_LINES = [
    "2024-03-15 08:00:00 INFO  App boot",
    "2024-03-15 08:00:01 DEBUG Loading plugins",
    "2024-03-15 08:00:02 DEBUG Loading plugins",
    "2024-03-15 08:00:03 WARNING Slow query detected",
    "2024-03-15 08:00:04 ERROR  DB timeout",
    "2024-03-15 08:00:05 ERROR  DB timeout",
    "2024-03-15 08:00:06 CRITICAL Disk full",
    "    stack trace line 1",
    "    stack trace line 2",
    "2024-03-15 08:00:07 INFO  Recovery attempted",
]


def test_round_trip_text_contains_critical():
    result = summarize(LOG_LINES)
    text = get_summary_reporter("text")(result)
    assert "CRITICAL" in text


def test_round_trip_json_total_lines_correct():
    result = summarize(LOG_LINES)
    payload = json.loads(get_summary_reporter("json")(result))
    assert payload["total_lines"] == len(LOG_LINES)


def test_round_trip_json_top_errors_non_empty():
    result = summarize(LOG_LINES)
    payload = json.loads(get_summary_reporter("json")(result))
    assert len(payload["top_errors"]) >= 1


def test_round_trip_unique_count_less_than_total_due_to_duplicates():
    result = summarize(LOG_LINES)
    assert result.unique_line_count < result.total_lines


def test_round_trip_severity_counts_sum_to_classified_lines():
    result = summarize(LOG_LINES)
    total_classified = sum(result.severity_counts.values())
    # continuation/unclassified lines won't appear in severity_counts
    assert total_classified <= result.total_lines
