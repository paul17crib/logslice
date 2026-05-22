"""Tests for logslice.splitter."""

from __future__ import annotations

import os
from datetime import timedelta

import pytest

from logslice.splitter import SplitResult, SplitSegment, split_by_window


LINES_TWO_HOURS = [
    "2024-01-10 08:00:00 INFO  booting up\n",
    "2024-01-10 08:15:00 DEBUG checkpoint\n",
    "2024-01-10 09:05:00 INFO  second hour\n",
    "2024-01-10 09:45:00 WARN  still second hour\n",
    "2024-01-10 10:01:00 ERROR third hour\n",
]


@pytest.fixture()
def out_dir(tmp_path):
    return str(tmp_path / "segments")


def test_split_returns_split_result(out_dir):
    result = split_by_window(iter(LINES_TWO_HOURS), out_dir, timedelta(hours=1))
    assert isinstance(result, SplitResult)


def test_split_correct_segment_count(out_dir):
    result = split_by_window(iter(LINES_TWO_HOURS), out_dir, timedelta(hours=1))
    assert result.segment_count == 3


def test_split_total_lines_matches_input(out_dir):
    result = split_by_window(iter(LINES_TWO_HOURS), out_dir, timedelta(hours=1))
    assert result.total_lines == len(LINES_TWO_HOURS)


def test_split_segments_are_split_segment_instances(out_dir):
    result = split_by_window(iter(LINES_TWO_HOURS), out_dir, timedelta(hours=1))
    for seg in result.segments:
        assert isinstance(seg, SplitSegment)


def test_split_segment_files_exist(out_dir):
    result = split_by_window(iter(LINES_TWO_HOURS), out_dir, timedelta(hours=1))
    for seg in result.segments:
        assert os.path.isfile(seg.path)


def test_split_segment_line_counts_sum_correctly(out_dir):
    result = split_by_window(iter(LINES_TWO_HOURS), out_dir, timedelta(hours=1))
    assert result.segments[0].line_count == 2
    assert result.segments[1].line_count == 2
    assert result.segments[2].line_count == 1


def test_split_output_dir_created_automatically(tmp_path):
    new_dir = str(tmp_path / "deep" / "nested" / "dir")
    split_by_window(iter(LINES_TWO_HOURS), new_dir, timedelta(hours=1))
    assert os.path.isdir(new_dir)


def test_split_empty_input_produces_no_segments(out_dir):
    result = split_by_window(iter([]), out_dir, timedelta(hours=1))
    assert result.segment_count == 0
    assert result.total_lines == 0


def test_split_custom_name_fn(out_dir):
    names = []

    def my_namer(idx, ts):
        name = f"custom_{idx:03d}"
        names.append(name)
        return name

    result = split_by_window(iter(LINES_TWO_HOURS), out_dir, timedelta(hours=1), name_fn=my_namer)
    for seg in result.segments:
        assert os.path.basename(seg.path).startswith("custom_")


def test_split_segment_start_timestamps_set(out_dir):
    result = split_by_window(iter(LINES_TWO_HOURS), out_dir, timedelta(hours=1))
    for seg in result.segments:
        assert seg.start is not None


def test_split_segment_end_before_or_equal_next_start(out_dir):
    result = split_by_window(iter(LINES_TWO_HOURS), out_dir, timedelta(hours=1))
    segs = result.segments
    for i in range(len(segs) - 1):
        assert segs[i].end <= segs[i + 1].start


def test_split_file_content_matches_lines(out_dir):
    result = split_by_window(iter(LINES_TWO_HOURS), out_dir, timedelta(hours=1))
    all_written = []
    for seg in result.segments:
        with open(seg.path, encoding="utf-8") as fh:
            all_written.extend(fh.readlines())
    stripped_input = [l if l.endswith("\n") else l + "\n" for l in LINES_TWO_HOURS]
    assert all_written == stripped_input
