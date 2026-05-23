"""Tests for logslice.filter_by_severity."""

import pytest
from logslice.filter_by_severity import FilterResult, filter_by_severity, iter_filter_by_severity


SAMPLE = [
    "DEBUG loading module",
    "INFO service ready",
    "WARNING low disk",
    "ERROR connection failed",
    "CRITICAL system down",
    "unclassified continuation line",
]


def test_filter_returns_filter_result():
    assert isinstance(filter_by_severity(SAMPLE), FilterResult)


def test_filter_no_bounds_keeps_all_classified_and_unclassified():
    result = filter_by_severity(SAMPLE)
    assert result.kept == len(SAMPLE)


def test_filter_min_warning_excludes_debug_info():
    result = filter_by_severity(SAMPLE, min_level="WARNING", include_unclassified=False)
    severities_kept = [l.split()[0] for l in result.lines]
    assert "DEBUG" not in severities_kept
    assert "INFO" not in severities_kept
    assert "WARNING" in severities_kept
    assert "ERROR" in severities_kept
    assert "CRITICAL" in severities_kept


def test_filter_max_warning_excludes_error_critical():
    result = filter_by_severity(SAMPLE, max_level="WARNING", include_unclassified=False)
    severities_kept = [l.split()[0] for l in result.lines]
    assert "ERROR" not in severities_kept
    assert "CRITICAL" not in severities_kept


def test_filter_exact_level():
    result = filter_by_severity(SAMPLE, min_level="ERROR", max_level="ERROR", include_unclassified=False)
    assert result.kept == 1
    assert "ERROR" in result.lines[0]


def test_filter_include_unclassified_true():
    result = filter_by_severity(SAMPLE, min_level="ERROR", include_unclassified=True)
    lines_text = " ".join(result.lines)
    assert "unclassified" in lines_text


def test_filter_include_unclassified_false():
    result = filter_by_severity(SAMPLE, min_level="ERROR", include_unclassified=False)
    lines_text = " ".join(result.lines)
    assert "unclassified" not in lines_text


def test_filter_rejected_count():
    result = filter_by_severity(SAMPLE, min_level="ERROR", include_unclassified=False)
    assert result.rejected == result.total_input - result.kept


def test_filter_empty_input():
    result = filter_by_severity([])
    assert result.total_input == 0
    assert result.kept == 0
    assert result.rejected == 0


def test_filter_invalid_level_raises():
    with pytest.raises(ValueError, match="Unknown severity"):
        filter_by_severity(SAMPLE, min_level="BOGUS")


def test_iter_filter_by_severity_yields_strings():
    gen = iter_filter_by_severity(["ERROR something", "INFO ok"], min_level="ERROR")
    results = list(gen)
    assert all(isinstance(r, str) for r in results)
    assert len(results) == 1
