"""Tests for logslice.grouper."""
import pytest
from logslice.grouper import (
    Group,
    GroupResult,
    group_by_pattern,
    group_by_time,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TIMED_LINES = [
    "2024-01-01T00:00:10 INFO  starting",
    "2024-01-01T00:00:45 DEBUG tick",
    "2024-01-01T00:01:05 INFO  running",
    "2024-01-01T00:01:55 WARN  slow",
    "2024-01-01T00:03:02 ERROR crash",
    "continuation line without timestamp",
]

PATTERN_LINES = [
    "2024-01-01 ERROR  disk full",
    "2024-01-01 INFO   started",
    "2024-01-01 ERROR  oom",
    "2024-01-01 DEBUG  verbose",
    "no level here at all",
]


# ---------------------------------------------------------------------------
# group_by_time
# ---------------------------------------------------------------------------

def test_group_by_time_returns_group_result():
    result = group_by_time(TIMED_LINES, window_seconds=60)
    assert isinstance(result, GroupResult)


def test_group_by_time_total_lines():
    result = group_by_time(TIMED_LINES, window_seconds=60)
    assert result.total_lines == len(TIMED_LINES)


def test_group_by_time_ungrouped_count():
    result = group_by_time(TIMED_LINES, window_seconds=60)
    assert result.ungrouped == 1


def test_group_by_time_correct_bucket_count():
    # 00:00, 00:01, 00:03 → 3 buckets
    result = group_by_time(TIMED_LINES, window_seconds=60)
    assert result.group_count == 3


def test_group_by_time_groups_are_group_instances():
    result = group_by_time(TIMED_LINES, window_seconds=60)
    assert all(isinstance(g, Group) for g in result.groups)


def test_group_by_time_groups_sorted():
    result = group_by_time(TIMED_LINES, window_seconds=60)
    keys = [g.key for g in result.groups]
    assert keys == sorted(keys)


def test_group_by_time_bucket_sizes():
    result = group_by_time(TIMED_LINES, window_seconds=60)
    sizes = {g.key[-5:]: g.size for g in result.groups}
    assert sizes["00:00"] == 2
    assert sizes["00:01"] == 2
    assert sizes["00:03"] == 1


def test_group_by_time_empty_input():
    result = group_by_time([], window_seconds=60)
    assert result.total_lines == 0
    assert result.group_count == 0
    assert result.ungrouped == 0


# ---------------------------------------------------------------------------
# group_by_pattern
# ---------------------------------------------------------------------------

def test_group_by_pattern_returns_group_result():
    result = group_by_pattern(PATTERN_LINES, pattern=r"(ERROR|WARN|INFO|DEBUG)")
    assert isinstance(result, GroupResult)


def test_group_by_pattern_total_lines():
    result = group_by_pattern(PATTERN_LINES, pattern=r"(ERROR|WARN|INFO|DEBUG)")
    assert result.total_lines == len(PATTERN_LINES)


def test_group_by_pattern_ungrouped_uses_fallback():
    result = group_by_pattern(PATTERN_LINES, pattern=r"(ERROR|WARN|INFO|DEBUG)")
    keys = {g.key for g in result.groups}
    assert "__other__" in keys


def test_group_by_pattern_error_group_has_two_lines():
    result = group_by_pattern(PATTERN_LINES, pattern=r"(ERROR|WARN|INFO|DEBUG)")
    error_groups = [g for g in result.groups if g.key.upper() == "ERROR"]
    assert len(error_groups) == 1
    assert error_groups[0].size == 2


def test_group_by_pattern_ungrouped_count():
    result = group_by_pattern(PATTERN_LINES, pattern=r"(ERROR|WARN|INFO|DEBUG)")
    assert result.ungrouped == 1


def test_group_by_pattern_custom_fallback_key():
    result = group_by_pattern(
        PATTERN_LINES,
        pattern=r"(ERROR|WARN|INFO|DEBUG)",
        fallback_key="UNKNOWN",
    )
    keys = {g.key for g in result.groups}
    assert "UNKNOWN" in keys


def test_group_by_pattern_empty_input():
    result = group_by_pattern([], pattern=r"(ERROR|WARN)")
    assert result.total_lines == 0
    assert result.group_count == 0
