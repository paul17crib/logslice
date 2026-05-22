"""Tests for logslice.sampler."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from logslice.sampler import SampleResult, sample_lines, sample_by_timestamp


TIMESTAMPED_LINES = [
    "2024-01-01T00:00:00Z INFO  boot started",
    "2024-01-01T00:00:05Z DEBUG step one",
    "2024-01-01T00:00:10Z DEBUG step two",
    "    continuation of step two",
    "2024-01-01T00:00:15Z INFO  step three",
    "2024-01-01T00:00:20Z WARN  almost done",
    "2024-01-01T00:00:25Z INFO  finished",
]


# ---------------------------------------------------------------------------
# sample_lines
# ---------------------------------------------------------------------------

def test_sample_lines_step_1_returns_all():
    result = sample_lines(TIMESTAMPED_LINES, step=1)
    assert result.lines == TIMESTAMPED_LINES
    assert result.total_visited == len(TIMESTAMPED_LINES)
    assert result.total_sampled == len(TIMESTAMPED_LINES)


def test_sample_lines_step_2_halves_output():
    result = sample_lines(TIMESTAMPED_LINES, step=2)
    assert result.total_sampled == (len(TIMESTAMPED_LINES) + 1) // 2
    assert result.lines[0] == TIMESTAMPED_LINES[0]


def test_sample_lines_max_lines_limits_output():
    result = sample_lines(TIMESTAMPED_LINES, step=1, max_lines=3)
    assert len(result.lines) == 3
    assert result.total_sampled == 3


def test_sample_lines_max_lines_and_step_combined():
    result = sample_lines(TIMESTAMPED_LINES, step=2, max_lines=2)
    assert len(result.lines) == 2


def test_sample_lines_empty_input():
    result = sample_lines([], step=1)
    assert result.lines == []
    assert result.total_visited == 0
    assert result.total_sampled == 0


def test_sample_lines_invalid_step_raises():
    with pytest.raises(ValueError, match="step must be >= 1"):
        sample_lines(TIMESTAMPED_LINES, step=0)


def test_sample_lines_returns_sample_result_instance():
    result = sample_lines(TIMESTAMPED_LINES)
    assert isinstance(result, SampleResult)


# ---------------------------------------------------------------------------
# sample_by_timestamp
# ---------------------------------------------------------------------------

def test_sample_by_timestamp_zero_interval_returns_all_timestamped():
    result = list(sample_by_timestamp(TIMESTAMPED_LINES, interval_seconds=0))
    timestamped = [l for l in TIMESTAMPED_LINES if not l.startswith(" ")]
    # continuation attached to the line before it
    assert len(result) >= len(timestamped)


def test_sample_by_timestamp_large_interval_returns_first():
    result = list(sample_by_timestamp(TIMESTAMPED_LINES, interval_seconds=9999))
    assert result[0] == TIMESTAMPED_LINES[0]
    assert len(result) == 1


def test_sample_by_timestamp_10s_interval():
    result = list(sample_by_timestamp(TIMESTAMPED_LINES, interval_seconds=10))
    # t=0, t=10 (with continuation), t=20 => 3 timestamped + 1 continuation
    assert any("boot started" in l for l in result)
    assert any("step two" in l for l in result)
    assert any("continuation" in l for l in result)


def test_sample_by_timestamp_continuation_not_emitted_when_parent_skipped():
    result = list(sample_by_timestamp(TIMESTAMPED_LINES, interval_seconds=9999))
    assert not any("continuation" in l for l in result)


def test_sample_by_timestamp_negative_interval_raises():
    with pytest.raises(ValueError, match="interval_seconds must be >= 0"):
        list(sample_by_timestamp(TIMESTAMPED_LINES, interval_seconds=-1))
