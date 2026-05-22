"""Integration tests: indexer + fast_slicer working together."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from logslice.indexer import build_index, seek_to_offset
from logslice.fast_slicer import fast_slice
from logslice.slicer import slice_log  # reference implementation


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


@pytest.fixture()
def large_log(tmp_path: Path) -> str:
    """Generate a synthetic log with 2 000 timestamped lines."""
    p = tmp_path / "large.log"
    lines = []
    base = datetime(2024, 6, 1, 0, 0, 0)
    for i in range(2000):
        from datetime import timedelta
        ts = (base + timedelta(seconds=i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        lines.append(f"{ts} INFO  event {i}\n")
    p.write_text("".join(lines), encoding="utf-8")
    return str(p)


def test_index_seek_offset_within_file(large_log):
    idx = build_index(large_log, sample_every=50)
    target = _dt("2024-06-01T00:10:00Z")
    offset = seek_to_offset(idx, target)
    import os
    assert 0 <= offset < os.path.getsize(large_log)


def test_fast_slice_with_index_matches_reference(large_log):
    start = _dt("2024-06-01T00:05:00Z")
    end = _dt("2024-06-01T00:15:00Z")

    idx = build_index(large_log, sample_every=50)
    indexed_result = list(fast_slice(large_log, start=start, end=end, index=idx))
    reference_result = list(slice_log(large_log, start=start, end=end))

    assert indexed_result == reference_result


def test_fast_slice_full_range_matches_reference(large_log):
    indexed_result = list(fast_slice(large_log))
    reference_result = list(slice_log(large_log))
    assert indexed_result == reference_result


def test_index_entries_cover_expected_range(large_log):
    idx = build_index(large_log, sample_every=100)
    first_ts = idx.entries[0][1]
    last_ts = idx.entries[-1][1]
    assert first_ts < last_ts
    assert first_ts >= _dt("2024-06-01T00:00:00Z")
