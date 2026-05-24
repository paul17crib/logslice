"""Tests for logslice.normalizer."""

import pytest
from logslice.normalizer import (
    NormalizeResult,
    iter_normalized,
    normalize,
)


def test_normalize_returns_normalize_result():
    result = normalize(["hello world"])
    assert isinstance(result, NormalizeResult)


def test_normalize_empty_input():
    result = normalize([])
    assert result.total == 0
    assert result.changed == 0
    assert result.lines == []


def test_normalize_strips_leading_trailing_spaces():
    result = normalize(["  hello  ", "  world  "])
    assert result.lines == ["hello", "world"]


def test_normalize_collapses_internal_whitespace():
    result = normalize(["hello   world"])
    assert result.lines == ["hello world"]


def test_normalize_strips_trailing_newline():
    result = normalize(["hello\n", "world\r\n"])
    assert result.lines == ["hello", "world"]


def test_normalize_lowercase_option():
    result = normalize(["Hello World", "FOO BAR"], lowercase=True)
    assert result.lines == ["hello world", "foo bar"]


def test_normalize_no_strip_keeps_surrounding_spaces():
    result = normalize(["  hello  "], strip=False)
    assert result.lines == ["  hello  "]


def test_normalize_no_collapse_keeps_multiple_spaces():
    result = normalize(["hello   world"], collapse_whitespace=False)
    assert result.lines == ["hello   world"]


def test_normalize_changed_count_correct():
    result = normalize(["hello", "  world  ", "foo   bar"])
    # "hello" unchanged, the other two are changed
    assert result.changed == 2


def test_normalize_unchanged_count():
    result = normalize(["hello", "world"])
    assert result.unchanged == 2


def test_normalize_total_count():
    result = normalize(["a", "b", "c"])
    assert result.total == 3


def test_change_ratio_all_changed():
    result = normalize(["  a  ", "  b  "])
    assert result.change_ratio == 1.0


def test_change_ratio_none_changed():
    result = normalize(["clean", "lines"])
    assert result.change_ratio == 0.0


def test_change_ratio_empty():
    result = normalize([])
    assert result.change_ratio == 0.0


def test_iter_normalized_yields_strings():
    out = list(iter_normalized(["  hello  ", "world\n"]))
    assert out == ["hello", "world"]


def test_iter_normalized_lazy():
    """iter_normalized should work on arbitrary iterables (e.g. generators)."""
    gen = (line for line in ["  a  ", "  b  "])
    out = list(iter_normalized(gen))
    assert out == ["a", "b"]


def test_iter_normalized_lowercase():
    out = list(iter_normalized(["UPPER CASE"], lowercase=True))
    assert out == ["upper case"]
