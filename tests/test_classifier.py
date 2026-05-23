"""Tests for logslice.classifier."""

import pytest
from logslice.classifier import (
    ClassifiedLine,
    ClassifyResult,
    SEVERITY_ORDER,
    classify,
    iter_classified,
)


SAMPLE_LINES = [
    "2024-01-01 INFO server started",
    "2024-01-01 DEBUG loading config",
    "2024-01-01 WARNING deprecated API used",
    "2024-01-01 ERROR failed to connect",
    "2024-01-01 CRITICAL fatal disk full",
    "2024-01-01 just a plain line",
]


def test_classify_returns_classify_result():
    result = classify(SAMPLE_LINES)
    assert isinstance(result, ClassifyResult)


def test_classify_total_count():
    result = classify(SAMPLE_LINES)
    assert result.total == len(SAMPLE_LINES)


def test_classify_classified_count():
    result = classify(SAMPLE_LINES)
    assert result.classified == 5  # all except plain line


def test_classify_unclassified_count():
    result = classify(SAMPLE_LINES)
    assert result.unclassified == 1


def test_classify_lines_are_classified_line_instances():
    result = classify(SAMPLE_LINES)
    assert all(isinstance(cl, ClassifiedLine) for cl in result.lines)


def test_classify_info_line():
    result = classify(["server started INFO"])
    assert result.lines[0].severity == "INFO"


def test_classify_error_line():
    result = classify(["ERROR: connection refused"])
    assert result.lines[0].severity == "ERROR"


def test_classify_critical_beats_info():
    # A line with both keywords should get highest-priority (CRITICAL)
    result = classify(["CRITICAL info fatal"])
    assert result.lines[0].severity == "CRITICAL"


def test_classify_plain_line_is_none():
    result = classify(["nothing special here"])
    assert result.lines[0].severity is None
    assert not result.lines[0].is_classified


def test_classify_empty_input():
    result = classify([])
    assert result.total == 0
    assert result.classified == 0
    assert result.unclassified == 0


def test_counts_by_severity_keys():
    result = classify(SAMPLE_LINES)
    counts = result.counts_by_severity()
    assert set(counts.keys()) == set(SEVERITY_ORDER)


def test_counts_by_severity_values():
    result = classify(SAMPLE_LINES)
    counts = result.counts_by_severity()
    assert counts["INFO"] == 1
    assert counts["DEBUG"] == 1
    assert counts["WARNING"] == 1
    assert counts["ERROR"] == 1
    assert counts["CRITICAL"] == 1


def test_iter_classified_yields_classified_lines():
    gen = iter_classified(["INFO ok", "plain"])
    first = next(gen)
    assert isinstance(first, ClassifiedLine)
    assert first.severity == "INFO"


def test_classify_custom_rules():
    rules = [("BOOM", r"\bexplosion\b")]
    result = classify(["there was an explosion", "all quiet"], rules=rules)
    assert result.lines[0].severity == "BOOM"
    assert result.lines[1].severity is None


def test_classify_case_sensitive_no_match():
    result = classify(["info server ready"], case_sensitive=True)
    # lowercase 'info' won't match \binfo\b with IGNORECASE off... actually it will
    # Let's test uppercase-only pattern with a non-matching case
    rules = [("INFO", r"\bINFO\b")]
    result2 = classify(["info server"], rules=rules, case_sensitive=True)
    assert result2.lines[0].severity is None
