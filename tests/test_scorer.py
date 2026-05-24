"""Tests for logslice.scorer and logslice.score_reporter."""
import json
import pytest

from logslice.scorer import ScoreResult, ScoredLine, score_lines
from logslice.score_reporter import (
    get_score_reporter,
    report_score_json,
    report_score_text,
)

LINES = [
    "ERROR: disk full on /dev/sda",
    "INFO: service started successfully",
    "WARNING: memory usage high",
    "DEBUG: entering loop iteration 42",
    "ERROR: connection refused to 10.0.0.1",
]

WEIGHTS = {"ERROR": 3.0, "WARNING": 1.5, "DEBUG": -1.0, "INFO": 0.5}


def test_score_lines_returns_score_result():
    result = score_lines(LINES, WEIGHTS)
    assert isinstance(result, ScoreResult)


def test_score_lines_total_lines():
    result = score_lines(LINES, WEIGHTS)
    assert result.total_lines == len(LINES)


def test_score_lines_all_kept_without_threshold():
    result = score_lines(LINES, WEIGHTS)
    assert result.scored_lines == len(LINES)


def test_score_lines_threshold_filters():
    result = score_lines(LINES, WEIGHTS, threshold=2.0)
    assert all(sl.score >= 2.0 for sl in result.lines)
    assert result.scored_lines < len(LINES)


def test_score_lines_matched_terms_populated():
    result = score_lines(["ERROR: boom"], {"ERROR": 5.0})
    assert result.lines[0].matched_terms == ["ERROR"]


def test_score_lines_no_match_score_zero():
    result = score_lines(["just a plain line"], WEIGHTS)
    assert result.lines[0].score == 0.0
    assert result.lines[0].matched_terms == []


def test_score_lines_negative_weight_applied():
    result = score_lines(["DEBUG: verbose output"], WEIGHTS)
    assert result.lines[0].score == pytest.approx(-1.0)


def test_score_lines_max_score():
    result = score_lines(LINES, WEIGHTS)
    expected_max = max(sl.score for sl in result.lines)
    assert result.max_score == pytest.approx(expected_max)


def test_score_lines_mean_score_empty():
    result = score_lines([], WEIGHTS)
    assert result.mean_score == 0.0


def test_score_lines_lines_are_scored_line_instances():
    result = score_lines(LINES, WEIGHTS)
    assert all(isinstance(sl, ScoredLine) for sl in result.lines)


def test_report_text_returns_string():
    result = score_lines(LINES, WEIGHTS)
    assert isinstance(report_score_text(result), str)


def test_report_text_contains_header():
    result = score_lines(LINES, WEIGHTS)
    assert "Score Report" in report_score_text(result)


def test_report_text_contains_total_lines():
    result = score_lines(LINES, WEIGHTS)
    text = report_score_text(result)
    assert str(result.total_lines) in text


def test_report_json_is_valid_json():
    result = score_lines(LINES, WEIGHTS)
    parsed = json.loads(report_score_json(result))
    assert isinstance(parsed, dict)


def test_report_json_has_lines_key():
    result = score_lines(LINES, WEIGHTS)
    parsed = json.loads(report_score_json(result))
    assert "lines" in parsed
    assert len(parsed["lines"]) == result.scored_lines


def test_get_score_reporter_text():
    fn = get_score_reporter("text")
    assert fn is report_score_text


def test_get_score_reporter_json():
    fn = get_score_reporter("json")
    assert fn is report_score_json


def test_get_score_reporter_invalid_raises():
    with pytest.raises(ValueError, match="Unknown format"):
        get_score_reporter("xml")
