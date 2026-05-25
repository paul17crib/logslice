"""Tests for logslice.transformer."""
from __future__ import annotations

import pytest

from logslice.transformer import (
    TransformResult,
    transform,
)


SAMPLE = ["Hello World", "foo bar", "  spaces  "]


def test_transform_returns_transform_result():
    result = transform(SAMPLE, [])
    assert isinstance(result, TransformResult)


def test_transform_empty_input():
    result = transform([], ["upper"])
    assert result.total_lines == 0
    assert result.changed_lines == 0
    assert result.lines == []


def test_transform_no_transforms_unchanged():
    result = transform(SAMPLE, [])
    assert result.lines == SAMPLE
    assert result.changed_lines == 0


def test_transform_upper():
    result = transform(["hello", "World"], ["upper"])
    assert result.lines == ["HELLO", "WORLD"]


def test_transform_lower():
    result = transform(["HELLO", "World"], ["lower"])
    assert result.lines == ["hello", "world"]


def test_transform_upper_changed_count():
    result = transform(["already", "UPPER"], ["upper"])
    # "already" changes, "UPPER" stays same
    assert result.changed_lines == 1


def test_transform_strip_ansi():
    ansi_line = "\x1b[31mERROR\x1b[0m message"
    result = transform([ansi_line], ["strip_ansi"])
    assert result.lines == ["ERROR message"]
    assert result.changed_lines == 1


def test_transform_strip_ansi_no_codes_unchanged():
    result = transform(["plain line"], ["strip_ansi"])
    assert result.changed_lines == 0


def test_transform_prefix():
    result = transform(["line1", "line2"], ["prefix:>> "])
    assert result.lines == [">> line1", ">> line2"]
    assert result.changed_lines == 2


def test_transform_suffix():
    result = transform(["line1"], ["suffix: END"])
    assert result.lines == ["line1 END"]


def test_transform_chained():
    result = transform(["Hello"], ["upper", "prefix:[LOG] "])
    assert result.lines == ["[LOG] HELLO"]


def test_transform_total_lines():
    result = transform(SAMPLE, ["lower"])
    assert result.total_lines == len(SAMPLE)


def test_transform_change_ratio_all_changed():
    result = transform(["abc", "def"], ["upper"])
    assert result.change_ratio == 1.0


def test_transform_change_ratio_none_changed():
    result = transform(["ABC", "DEF"], ["upper"])
    assert result.change_ratio == 0.0


def test_transform_unknown_raises():
    with pytest.raises(ValueError, match="Unknown transform"):
        transform(["line"], ["nonexistent_transform"])


def test_transform_extra_callable():
    def reverse(line: str) -> str:
        return line[::-1]

    result = transform(["abc"], [], extra=[reverse])
    assert result.lines == ["cba"]
    assert result.changed_lines == 1


def test_transform_transforms_applied_names():
    result = transform(["x"], ["upper", "lower"])
    assert "_make_upper" in result.transforms_applied or "upper" in str(result.transforms_applied)
    assert len(result.transforms_applied) == 2
