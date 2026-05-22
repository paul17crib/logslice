"""Tests for logslice.compressor."""

from __future__ import annotations

import pytest

from logslice.compressor import (
    CompressResult,
    compress,
    iter_compressed,
)


# ---------------------------------------------------------------------------
# compress() – result type and basic behaviour
# ---------------------------------------------------------------------------

def test_compress_returns_compress_result():
    result = compress(["a", "b"])
    assert isinstance(result, CompressResult)


def test_compress_empty_input():
    result = compress([])
    assert result.lines == []
    assert result.original_count == 0
    assert result.compressed_count == 0
    assert result.collapsed_runs == 0


def test_compress_no_duplicates_unchanged():
    lines = ["alpha", "beta", "gamma"]
    result = compress(lines)
    assert result.lines == lines
    assert result.collapsed_runs == 0


def test_compress_single_line_no_duplicate():
    result = compress(["only line"])
    assert result.lines == ["only line"]
    assert result.original_count == 1


def test_compress_run_of_two_collapsed():
    lines = ["err", "err"]
    result = compress(lines)
    assert len(result.lines) == 1
    assert "x2" in result.lines[0]
    assert result.collapsed_runs == 1


def test_compress_run_below_min_run_not_collapsed():
    # min_run=3 means a run of 2 should NOT be collapsed
    lines = ["warn", "warn"]
    result = compress(lines, min_run=3)
    assert result.lines == ["warn", "warn"]
    assert result.collapsed_runs == 0


def test_compress_long_run_single_output_line():
    lines = ["repeat"] * 10
    result = compress(lines)
    assert len(result.lines) == 1
    assert "x10" in result.lines[0]
    assert result.collapsed_runs == 1


def test_compress_multiple_runs():
    lines = ["a", "a", "b", "b", "b"]
    result = compress(lines)
    assert result.collapsed_runs == 2
    assert len(result.lines) == 2


def test_compress_mixed_runs_and_unique():
    lines = ["x", "y", "y", "z"]
    result = compress(lines)
    # 'y' run collapsed → ['x', 'y [x2]', 'z']
    assert len(result.lines) == 3
    assert result.lines[0] == "x"
    assert result.lines[2] == "z"


def test_compress_ratio_zero_when_nothing_removed():
    result = compress(["a", "b", "c"])
    assert result.ratio == 0.0


def test_compress_ratio_nonzero_after_collapse():
    lines = ["dup"] * 4
    result = compress(lines)
    assert result.ratio > 0.0


def test_compress_custom_template():
    lines = ["msg", "msg", "msg"]
    result = compress(lines, template="{line} (repeated {count}x)")
    assert "repeated 3x" in result.lines[0]


def test_compress_strips_trailing_newline():
    lines = ["line\n", "line\n"]
    result = compress(lines)
    assert "line" in result.lines[0]
    assert "\n" not in result.lines[0]


# ---------------------------------------------------------------------------
# iter_compressed() – streaming interface
# ---------------------------------------------------------------------------

def test_iter_compressed_yields_strings():
    out = list(iter_compressed(["a", "a"]))
    assert all(isinstance(s, str) for s in out)


def test_iter_compressed_matches_compress_output():
    lines = ["p", "p", "q", "r", "r", "r"]
    assert list(iter_compressed(lines)) == compress(lines).lines


def test_iter_compressed_empty():
    assert list(iter_compressed([])) == []
