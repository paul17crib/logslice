"""Tests for logslice.annotator."""

import pytest

from logslice.annotator import AnnotatedLine, AnnotateResult, annotate, iter_annotated

RULES = [
    (r"ERROR", "error"),
    (r"WARN", "warning"),
    (r"\d{3}", "has_code"),
]

SAMPLE_LINES = [
    "2024-01-01 ERROR something broke",
    "2024-01-01 WARN disk low",
    "2024-01-01 INFO all good",
    "2024-01-01 ERROR code 500 returned",
]


def test_annotate_returns_annotate_result():
    result = annotate(SAMPLE_LINES, RULES)
    assert isinstance(result, AnnotateResult)


def test_annotate_total_count():
    result = annotate(SAMPLE_LINES, RULES)
    assert result.total == len(SAMPLE_LINES)


def test_annotate_annotated_count():
    result = annotate(SAMPLE_LINES, RULES)
    # INFO line has no match; the rest do
    assert result.annotated == 3


def test_annotate_unannotated_count():
    result = annotate(SAMPLE_LINES, RULES)
    assert result.unannotated == 1


def test_annotate_error_tag_applied():
    result = annotate(SAMPLE_LINES, RULES)
    assert "error" in result.lines[0].tags


def test_annotate_warning_tag_applied():
    result = annotate(SAMPLE_LINES, RULES)
    assert "warning" in result.lines[1].tags


def test_annotate_info_line_has_no_tags():
    result = annotate(SAMPLE_LINES, RULES)
    assert result.lines[2].tags == []
    assert not result.lines[2].is_annotated


def test_annotate_multiple_tags_on_one_line():
    result = annotate(SAMPLE_LINES, RULES)
    # "ERROR code 500 returned" matches both 'error' and 'has_code'
    tags = result.lines[3].tags
    assert "error" in tags
    assert "has_code" in tags


def test_annotate_tag_all_false_stops_at_first_match():
    result = annotate(SAMPLE_LINES, RULES, tag_all=False)
    # The last line matches ERROR first; should not also have has_code
    tags = result.lines[3].tags
    assert len(tags) == 1
    assert tags[0] == "error"


def test_annotate_case_sensitive_no_match():
    lines = ["error lowercase only"]
    result = annotate(lines, [(r"ERROR", "error")], case_sensitive=True)
    assert result.annotated == 0


def test_annotate_case_insensitive_matches():
    lines = ["error lowercase only"]
    result = annotate(lines, [(r"ERROR", "error")], case_sensitive=False)
    assert result.annotated == 1


def test_annotate_empty_input():
    result = annotate([], RULES)
    assert result.total == 0
    assert result.annotated == 0
    assert result.lines == []


def test_iter_annotated_yields_annotated_line_instances():
    for al in iter_annotated(SAMPLE_LINES, RULES):
        assert isinstance(al, AnnotatedLine)


def test_annotated_line_is_annotated_property():
    tagged = AnnotatedLine(line="foo", tags=["error"])
    untagged = AnnotatedLine(line="bar", tags=[])
    assert tagged.is_annotated
    assert not untagged.is_annotated
