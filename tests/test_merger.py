"""Tests for logslice.merger — chronological log merging."""

from __future__ import annotations

import pytest

from logslice.merger import merge_logs


LOG_A = [
    "2024-01-01 10:00:00 alpha start",
    "2024-01-01 10:00:02 alpha middle",
    "2024-01-01 10:00:05 alpha end",
]

LOG_B = [
    "2024-01-01 10:00:01 beta first",
    "2024-01-01 10:00:03 beta second",
    "2024-01-01 10:00:06 beta last",
]


def test_merge_two_sources_chronological_order():
    result = list(merge_logs([("A", iter(LOG_A)), ("B", iter(LOG_B))]))
    assert len(result) == 6
    # Verify timestamps are non-decreasing by checking keyword order
    keywords = [line.split()[2] for line in result]
    assert keywords == ["alpha", "beta", "alpha", "beta", "alpha", "beta"]


def test_merge_empty_sources_returns_empty():
    result = list(merge_logs([]))
    assert result == []


def test_merge_single_source_passthrough():
    result = list(merge_logs([("only", iter(LOG_A))]))
    assert result == LOG_A


def test_merge_one_empty_source():
    result = list(merge_logs([("A", iter(LOG_A)), ("empty", iter([]))]))
    assert result == LOG_A


def test_merge_tag_prefixes_source_label():
    result = list(merge_logs([("A", iter(LOG_A)), ("B", iter(LOG_B))], tag=True))
    assert all(line.startswith("[A] ") or line.startswith("[B] ") for line in result)
    assert result[0].startswith("[A] ")
    assert result[1].startswith("[B] ")


def test_merge_tag_false_no_prefix():
    result = list(merge_logs([("A", iter(LOG_A))], tag=False))
    assert not any(line.startswith("[") for line in result)


def test_merge_lines_without_timestamps_sort_last():
    log_with_plain = [
        "continuation line no timestamp",
        "another plain line",
    ]
    result = list(merge_logs([("A", iter(LOG_A)), ("plain", iter(log_with_plain))]))
    # Plain lines should appear after all timestamped lines
    assert result[:3] == LOG_A
    assert "continuation line no timestamp" in result
    assert "another plain line" in result


def test_merge_identical_timestamps_stable_by_source_order():
    ts = "2024-01-01 10:00:00"
    log_x = [f"{ts} X line"]
    log_y = [f"{ts} Y line"]
    result = list(merge_logs([("X", iter(log_x)), ("Y", iter(log_y))]))
    assert len(result) == 2
    assert "X line" in result[0]
    assert "Y line" in result[1]


def test_merge_returns_all_lines():
    result = list(merge_logs([("A", iter(LOG_A)), ("B", iter(LOG_B))]))
    assert len(result) == len(LOG_A) + len(LOG_B)
