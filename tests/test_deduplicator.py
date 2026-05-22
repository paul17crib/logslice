"""Tests for logslice.deduplicator."""

import pytest

from logslice.deduplicator import (
    DedupeResult,
    deduplicate,
    iter_deduplicated,
)


# ---------------------------------------------------------------------------
# deduplicate — global mode (consecutive_only=False)
# ---------------------------------------------------------------------------

def test_deduplicate_removes_all_duplicates():
    lines = ["a", "b", "a", "c", "b"]
    result = deduplicate(lines)
    assert result.lines == ["a", "b", "c"]


def test_deduplicate_returns_deduperesult_instance():
    result = deduplicate(["x", "y"])
    assert isinstance(result, DedupeResult)


def test_deduplicate_counts_are_correct():
    lines = ["a", "a", "b", "a"]
    result = deduplicate(lines)
    assert result.total_input == 4
    assert result.duplicate_count == 2
    assert result.unique_count == 2


def test_deduplicate_empty_input():
    result = deduplicate([])
    assert result.lines == []
    assert result.total_input == 0
    assert result.duplicate_count == 0
    assert result.unique_count == 0


def test_deduplicate_no_duplicates_unchanged():
    lines = ["a", "b", "c"]
    result = deduplicate(lines)
    assert result.lines == ["a", "b", "c"]
    assert result.duplicate_count == 0


def test_deduplicate_keep_last():
    lines = ["a", "b", "a"]
    result = deduplicate(lines, keep="last")
    # 'a' should appear at the end
    assert result.lines == ["b", "a"]
    assert result.duplicate_count == 1


def test_deduplicate_invalid_keep_raises():
    with pytest.raises(ValueError, match="keep must be"):
        deduplicate(["a"], keep="middle")


# ---------------------------------------------------------------------------
# deduplicate — consecutive mode
# ---------------------------------------------------------------------------

def test_deduplicate_consecutive_only_collapses_runs():
    lines = ["a", "a", "b", "b", "b", "a"]
    result = deduplicate(lines, consecutive_only=True)
    assert result.lines == ["a", "b", "a"]
    assert result.duplicate_count == 3


def test_deduplicate_consecutive_keeps_non_adjacent_duplicates():
    lines = ["a", "b", "a"]
    result = deduplicate(lines, consecutive_only=True)
    # non-adjacent 'a' is NOT removed
    assert result.lines == ["a", "b", "a"]
    assert result.duplicate_count == 0


# ---------------------------------------------------------------------------
# iter_deduplicated (streaming)
# ---------------------------------------------------------------------------

def test_iter_deduplicated_yields_unique_consecutive():
    lines = ["x", "x", "y", "z", "z", "z", "y"]
    result = list(iter_deduplicated(lines))
    assert result == ["x", "y", "z", "y"]


def test_iter_deduplicated_empty():
    assert list(iter_deduplicated([])) == []


def test_iter_deduplicated_all_same():
    assert list(iter_deduplicated(["a"] * 5)) == ["a"]


def test_iter_deduplicated_is_iterator():
    import types
    gen = iter_deduplicated(["a", "b"])
    assert isinstance(gen, types.GeneratorType)


def test_iter_deduplicated_single_element():
    assert list(iter_deduplicated(["only"])) == ["only"]


def test_iter_deduplicated_no_consecutive_duplicates():
    """Lines that alternate should all be yielded unchanged."""
    lines = ["a", "b", "a", "b", "a"]
    assert list(iter_deduplicated(lines)) == ["a", "b", "a", "b", "a"]
