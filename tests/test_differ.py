"""Tests for logslice.differ."""
import pytest

from logslice.differ import DiffLine, DiffResult, diff_logs


LINES_A = ["alpha", "bravo", "charlie", "delta"]
LINES_B = ["alpha", "bravo", "echo", "delta"]


def test_diff_returns_diff_result():
    result = diff_logs(LINES_A, LINES_B)
    assert isinstance(result, DiffResult)


def test_diff_lines_are_diff_line_instances():
    result = diff_logs(LINES_A, LINES_B)
    assert all(isinstance(dl, DiffLine) for dl in result.lines)


def test_diff_identical_sequences_no_changes():
    result = diff_logs(LINES_A, LINES_A)
    assert result.added == 0
    assert result.removed == 0
    assert result.equal == len(LINES_A)


def test_diff_detects_insertion():
    result = diff_logs(["a", "b"], ["a", "x", "b"])
    assert result.added >= 1


def test_diff_detects_deletion():
    result = diff_logs(["a", "x", "b"], ["a", "b"])
    assert result.removed >= 1


def test_diff_replace_counts_both_sides():
    result = diff_logs(LINES_A, LINES_B)
    # 'charlie' removed, 'echo' added
    assert result.removed >= 1
    assert result.added >= 1


def test_diff_empty_a_all_insertions():
    result = diff_logs([], ["a", "b", "c"])
    assert result.added == 3
    assert result.removed == 0
    assert result.equal == 0


def test_diff_empty_b_all_deletions():
    result = diff_logs(["a", "b", "c"], [])
    assert result.removed == 3
    assert result.added == 0


def test_diff_both_empty():
    result = diff_logs([], [])
    assert result.added == 0
    assert result.removed == 0
    assert result.equal == 0
    assert result.total == 0


def test_change_ratio_zero_for_identical():
    result = diff_logs(["x"], ["x"])
    assert result.change_ratio == 0.0


def test_change_ratio_one_for_full_replacement():
    result = diff_logs(["a"], ["b"])
    # one delete + one insert; equal = 0 → ratio = 2/2 = 1.0
    assert result.change_ratio == 1.0


def test_change_ratio_empty_input_is_zero():
    result = diff_logs([], [])
    assert result.change_ratio == 0.0


def test_total_equals_sum_of_parts():
    result = diff_logs(LINES_A, LINES_B)
    assert result.total == result.added + result.removed + result.equal


def test_diff_tag_values_are_valid():
    valid_tags = {"equal", "insert", "delete"}
    result = diff_logs(LINES_A, LINES_B)
    for dl in result.lines:
        assert dl.tag in valid_tags


def test_diff_source_values_are_valid():
    result = diff_logs(LINES_A, LINES_B)
    for dl in result.lines:
        assert dl.source in {"a", "b", "both"}
