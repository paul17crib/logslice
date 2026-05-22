"""Tests for logslice.truncator."""

from __future__ import annotations

import pytest

from logslice.truncator import (
    TruncateResult,
    iter_truncated,
    truncate,
)


# ---------------------------------------------------------------------------
# truncate() – result type and basic counts
# ---------------------------------------------------------------------------

def test_truncate_returns_truncate_result():
    result = truncate(["hello\n"])
    assert isinstance(result, TruncateResult)


def test_truncate_empty_input():
    result = truncate([])
    assert result.lines == []
    assert result.total_lines == 0
    assert result.truncated_lines == 0


def test_truncate_no_lines_exceed_width():
    lines = ["short\n", "also short\n"]
    result = truncate(lines, max_width=80)
    assert result.truncated_lines == 0
    assert result.total_lines == 2
    assert result.lines == lines


def test_truncate_all_lines_exceed_width():
    lines = ["abcdefgh\n", "12345678\n"]
    result = truncate(lines, max_width=4, suffix="...")
    assert result.truncated_lines == 2
    assert result.lines == ["abcd...\n", "1234...\n"]


def test_truncate_partial_lines_exceed_width():
    lines = ["hi\n", "this is a very long line indeed\n"]
    result = truncate(lines, max_width=10, suffix="~")
    assert result.truncated_lines == 1
    assert result.total_lines == 2
    assert result.lines[0] == "hi\n"
    assert result.lines[1] == "this is a ~\n"


def test_truncate_preserves_newline():
    result = truncate(["abcdef\n"], max_width=3, suffix="...")
    assert result.lines[0].endswith("\n")


def test_truncate_no_trailing_newline():
    result = truncate(["abcdef"], max_width=3, suffix="...")
    assert not result.lines[0].endswith("\n")
    assert result.lines[0] == "abc..."


# ---------------------------------------------------------------------------
# truncation_ratio property
# ---------------------------------------------------------------------------

def test_truncation_ratio_zero_when_no_truncation():
    result = truncate(["short\n"], max_width=100)
    assert result.truncation_ratio == 0.0


def test_truncation_ratio_one_when_all_truncated():
    result = truncate(["abcde\n", "fghij\n"], max_width=2, suffix="!")
    assert result.truncation_ratio == 1.0


def test_truncation_ratio_empty_input_is_zero():
    result = truncate([])
    assert result.truncation_ratio == 0.0


# ---------------------------------------------------------------------------
# iter_truncated() – streaming interface
# ---------------------------------------------------------------------------

def test_iter_truncated_yields_strings():
    lines = ["hello world\n", "foo\n"]
    out = list(iter_truncated(lines, max_width=5, suffix=".."))
    assert all(isinstance(l, str) for l in out)


def test_iter_truncated_truncates_long_lines():
    out = list(iter_truncated(["abcdefgh\n"], max_width=4, suffix="..."))
    assert out == ["abcd...\n"]


def test_iter_truncated_passes_short_lines_unchanged():
    lines = ["ok\n", "fine\n"]
    out = list(iter_truncated(lines, max_width=80))
    assert out == lines


# ---------------------------------------------------------------------------
# Invalid max_width
# ---------------------------------------------------------------------------

def test_truncate_invalid_max_width_raises():
    with pytest.raises(ValueError):
        truncate(["line\n"], max_width=0)


def test_iter_truncated_invalid_max_width_raises():
    with pytest.raises(ValueError):
        list(iter_truncated(["line\n"], max_width=-5))
