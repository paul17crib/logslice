"""Tests for logslice.indexer."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone

import pytest

from logslice.indexer import LogIndex, build_index, seek_to_offset, index_file_size


TIMESTAMPED_LINES = [
    "2024-01-01T00:00:00Z INFO  boot started\n",
    "2024-01-01T00:01:00Z DEBUG loop iteration 1\n",
    "2024-01-01T00:02:00Z DEBUG loop iteration 2\n",
    "2024-01-01T00:03:00Z WARN  something odd\n",
    "2024-01-01T00:04:00Z ERROR crash\n",
]


@pytest.fixture()
def log_path(tmp_path):
    p = tmp_path / "sample.log"
    p.write_text("".join(TIMESTAMPED_LINES), encoding="utf-8")
    return str(p)


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


# ---------------------------------------------------------------------------
# build_index
# ---------------------------------------------------------------------------

def test_build_index_returns_log_index(log_path):
    idx = build_index(log_path, sample_every=1)
    assert isinstance(idx, LogIndex)


def test_build_index_entries_sorted_by_offset(log_path):
    idx = build_index(log_path, sample_every=1)
    offsets = [e[0] for e in idx.entries]
    assert offsets == sorted(offsets)


def test_build_index_timestamps_non_decreasing(log_path):
    idx = build_index(log_path, sample_every=1)
    timestamps = [e[1] for e in idx.entries]
    assert timestamps == sorted(timestamps)


def test_build_index_sample_every_reduces_entries(log_path):
    idx_dense = build_index(log_path, sample_every=1)
    idx_sparse = build_index(log_path, sample_every=3)
    assert len(idx_sparse) <= len(idx_dense)


def test_build_index_empty_file(tmp_path):
    p = tmp_path / "empty.log"
    p.write_text("", encoding="utf-8")
    idx = build_index(str(p), sample_every=1)
    assert idx.is_empty()


# ---------------------------------------------------------------------------
# seek_to_offset
# ---------------------------------------------------------------------------

def test_seek_to_offset_empty_index_returns_zero():
    idx = LogIndex()
    assert seek_to_offset(idx, _dt("2024-01-01T00:02:00Z")) == 0


def test_seek_to_offset_before_first_entry_returns_zero(log_path):
    idx = build_index(log_path, sample_every=1)
    offset = seek_to_offset(idx, _dt("2023-12-31T23:59:59Z"))
    assert offset == 0


def test_seek_to_offset_returns_non_negative(log_path):
    idx = build_index(log_path, sample_every=1)
    offset = seek_to_offset(idx, _dt("2024-01-01T00:02:30Z"))
    assert offset >= 0


# ---------------------------------------------------------------------------
# index_file_size
# ---------------------------------------------------------------------------

def test_index_file_size_matches_os(log_path):
    assert index_file_size(log_path) == os.path.getsize(log_path)
