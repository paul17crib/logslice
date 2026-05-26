"""Tests for logslice.matcher."""
import pytest
from logslice.matcher import MatchedLine, MatchResult, match_lines


SAMPLE_LINES = [
    "2024-01-01 INFO  service started",
    "2024-01-01 DEBUG polling endpoint",
    "2024-01-01 ERROR connection refused",
    "2024-01-01 WARN  disk usage high",
    "2024-01-01 ERROR timeout reached",
    "2024-01-01 INFO  service stopped",
]


def test_match_lines_returns_match_result():
    result = match_lines(SAMPLE_LINES, ["ERROR"])
    assert isinstance(result, MatchResult)


def test_match_lines_are_matched_line_instances():
    result = match_lines(SAMPLE_LINES, ["ERROR"])
    for ml in result.lines:
        assert isinstance(ml, MatchedLine)


def test_match_lines_total_input_correct():
    result = match_lines(SAMPLE_LINES, ["ERROR"])
    assert result.total_input == len(SAMPLE_LINES)


def test_match_lines_match_count_correct():
    result = match_lines(SAMPLE_LINES, ["ERROR"])
    assert result.match_count == 2


def test_match_lines_match_ratio():
    result = match_lines(SAMPLE_LINES, ["ERROR"])
    assert abs(result.match_ratio - 2 / 6) < 1e-9


def test_match_lines_pattern_counts_populated():
    result = match_lines(SAMPLE_LINES, ["ERROR"])
    assert result.pattern_counts["ERROR"] == 2


def test_match_lines_case_insensitive_default():
    result = match_lines(SAMPLE_LINES, ["error"])
    assert result.match_count == 2


def test_match_lines_case_sensitive_no_match():
    result = match_lines(SAMPLE_LINES, ["error"], case_sensitive=True)
    assert result.match_count == 0


def test_match_lines_case_sensitive_match():
    result = match_lines(SAMPLE_LINES, ["ERROR"], case_sensitive=True)
    assert result.match_count == 2


def test_match_lines_span_is_tuple():
    result = match_lines(SAMPLE_LINES, ["ERROR"])
    for ml in result.lines:
        assert isinstance(ml.span, tuple)
        assert len(ml.span) == 2


def test_match_lines_line_numbers_are_positive():
    result = match_lines(SAMPLE_LINES, ["ERROR"])
    for ml in result.lines:
        assert ml.line_number >= 1


def test_match_lines_or_logic_multiple_patterns():
    result = match_lines(SAMPLE_LINES, ["ERROR", "WARN"])
    assert result.match_count == 3


def test_match_lines_and_logic_match_all():
    lines = ["ERROR timeout", "ERROR connection", "WARN timeout"]
    result = match_lines(lines, ["ERROR", "timeout"], match_all=True)
    assert result.match_count == 1
    assert result.lines[0].line == "ERROR timeout"


def test_match_lines_no_patterns_raises():
    with pytest.raises(ValueError, match="pattern"):
        match_lines(SAMPLE_LINES, [])


def test_match_lines_invalid_pattern_raises():
    with pytest.raises(ValueError, match="Invalid pattern"):
        match_lines(SAMPLE_LINES, ["["])


def test_match_lines_empty_input():
    result = match_lines([], ["ERROR"])
    assert result.total_input == 0
    assert result.match_count == 0
    assert result.match_ratio == 0.0


def test_matched_line_is_match_property():
    result = match_lines(SAMPLE_LINES, ["INFO"])
    for ml in result.lines:
        assert ml.is_match is True


def test_match_lines_pattern_stored_on_matched_line():
    result = match_lines(SAMPLE_LINES, ["WARN"])
    assert result.lines[0].pattern == "WARN"
