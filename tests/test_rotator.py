"""Tests for logslice.rotator."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from logslice.rotator import (
    RotationResult,
    RotatedSegment,
    find_rotated_segments,
)


@pytest.fixture()
def log_dir(tmp_path: Path) -> Path:
    """Create a directory with a family of rotated log files."""
    (tmp_path / "app.log").write_text("current\n")
    (tmp_path / "app.log.1").write_text("rotation 1\n")
    (tmp_path / "app.log.2").write_text("rotation 2\n")
    (tmp_path / "app.log.3").write_text("rotation 3\n")
    (tmp_path / "app.log.3.gz").write_bytes(b"\x1f\x8b")   # unrelated gz stub
    (tmp_path / "other.log").write_text("unrelated\n")
    return tmp_path


def test_find_rotated_returns_rotation_result(log_dir: Path) -> None:
    result = find_rotated_segments(log_dir / "app.log")
    assert isinstance(result, RotationResult)


def test_find_rotated_base_path_stored(log_dir: Path) -> None:
    result = find_rotated_segments(log_dir / "app.log")
    assert result.base == log_dir / "app.log"


def test_find_rotated_includes_current_file(log_dir: Path) -> None:
    result = find_rotated_segments(log_dir / "app.log")
    indices = [s.index for s in result.segments]
    assert 0 in indices


def test_find_rotated_excludes_unrelated_files(log_dir: Path) -> None:
    result = find_rotated_segments(log_dir / "app.log")
    paths = [s.path.name for s in result.segments]
    assert "other.log" not in paths


def test_find_rotated_segments_ordered_oldest_first(log_dir: Path) -> None:
    result = find_rotated_segments(log_dir / "app.log")
    indices = [s.index for s in result.segments]
    assert indices == sorted(indices, reverse=True)


def test_find_rotated_count_matches_family(log_dir: Path) -> None:
    result = find_rotated_segments(log_dir / "app.log")
    # app.log (0), app.log.1, app.log.2, app.log.3, app.log.3.gz = 5 members
    assert result.count == 5


def test_find_rotated_total_size_positive(log_dir: Path) -> None:
    result = find_rotated_segments(log_dir / "app.log")
    assert result.total_size > 0


def test_find_rotated_max_segments_limits_output(log_dir: Path) -> None:
    result = find_rotated_segments(log_dir / "app.log", max_segments=2)
    assert result.count <= 2


def test_find_rotated_each_segment_is_rotated_segment(log_dir: Path) -> None:
    result = find_rotated_segments(log_dir / "app.log")
    for seg in result.segments:
        assert isinstance(seg, RotatedSegment)


def test_find_rotated_missing_directory_returns_empty(tmp_path: Path) -> None:
    result = find_rotated_segments(tmp_path / "nonexistent" / "app.log")
    assert result.count == 0


def test_find_rotated_single_file_only(tmp_path: Path) -> None:
    (tmp_path / "app.log").write_text("only\n")
    result = find_rotated_segments(tmp_path / "app.log")
    assert result.count == 1
    assert result.segments[0].index == 0
