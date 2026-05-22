"""Tests for logslice.fast_slicer."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from logslice.fast_slicer import fast_slice, fast_slice_with_index


LINES = [
    "2024-03-01T10:00:00Z INFO  alpha\n",
    "  continuation of alpha\n",
    "2024-03-01T10:01:00Z DEBUG beta\n",
    "2024-03-01T10:02:00Z WARN  gamma\n",
    "2024-03-01T10:03:00Z ERROR delta\n",
]


@pytest.fixture()
def log_path(tmp_path: Path) -> str:
    p = tmp_path / "test.log"
    p.write_text("".join(LINES), encoding="utf-8")
    return str(p)


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def test_fast_slice_no_bounds_returns_all(log_path):
    result = list(fast_slice(log_path))
    assert result == LINES


def test_fast_slice_start_only(log_path):
    result = list(fast_slice(log_path, start=_dt("2024-03-01T10:02:00Z")))
    assert any("gamma" in l for l in result)
    assert any("delta" in l for l in result)
    assert not any("alpha" in l for l in result)


def test_fast_slice_end_only(log_path):
    result = list(fast_slice(log_path, end=_dt("2024-03-01T10:01:00Z")))
    assert any("alpha" in l for l in result)
    assert any("beta" in l for l in result)
    assert not any("gamma" in l for l in result)


def test_fast_slice_start_and_end(log_path):
    result = list(
        fast_slice(
            log_path,
            start=_dt("2024-03-01T10:01:00Z"),
            end=_dt("2024-03-01T10:02:00Z"),
        )
    )
    assert any("beta" in l for l in result)
    assert any("gamma" in l for l in result)
    assert not any("alpha" in l for l in result)
    assert not any("delta" in l for l in result)


def test_fast_slice_continuation_lines_included(log_path):
    result = list(fast_slice(log_path, end=_dt("2024-03-01T10:01:00Z")))
    assert any("continuation" in l for l in result)


def test_fast_slice_empty_range(log_path):
    result = list(
        fast_slice(
            log_path,
            start=_dt("2024-03-01T12:00:00Z"),
            end=_dt("2024-03-01T13:00:00Z"),
        )
    )
    assert result == []


def test_fast_slice_with_index_matches_fast_slice(log_path):
    expected = list(fast_slice(log_path))
    result = list(fast_slice_with_index(log_path, sample_every=1))
    assert result == expected
