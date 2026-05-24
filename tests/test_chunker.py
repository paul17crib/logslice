"""Tests for logslice.chunker."""
from __future__ import annotations

from datetime import timedelta

import pytest

from logslice.chunker import Chunk, ChunkResult, chunk


LINES = [
    "2024-01-01T00:00:00 alpha",
    "2024-01-01T00:00:01 bravo",
    "2024-01-01T00:00:02 charlie",
    "2024-01-01T00:00:03 delta",
    "2024-01-01T00:00:04 echo",
]


def test_chunk_returns_chunk_result():
    result = chunk(LINES, chunk_size=2)
    assert isinstance(result, ChunkResult)


def test_chunk_size_correct_count():
    result = chunk(LINES, chunk_size=2)
    assert result.chunk_count == 3  # 2, 2, 1


def test_chunk_size_total_lines():
    result = chunk(LINES, chunk_size=2)
    assert result.total_lines == len(LINES)


def test_chunk_size_last_chunk_smaller():
    result = chunk(LINES, chunk_size=2)
    assert result.chunks[-1].size == 1


def test_chunk_size_chunks_are_chunk_instances():
    result = chunk(LINES, chunk_size=3)
    assert all(isinstance(c, Chunk) for c in result.chunks)


def test_chunk_size_indices_sequential():
    result = chunk(LINES, chunk_size=2)
    indices = [c.index for c in result.chunks]
    assert indices == list(range(result.chunk_count))


def test_chunk_size_exact_division():
    result = chunk(LINES[:4], chunk_size=2)
    assert result.chunk_count == 2
    assert all(c.size == 2 for c in result.chunks)


def test_chunk_empty_input_size():
    result = chunk([], chunk_size=5)
    assert result.chunk_count == 0
    assert result.total_lines == 0


def test_chunk_time_window_returns_chunk_result():
    result = chunk(LINES, window=timedelta(seconds=2))
    assert isinstance(result, ChunkResult)


def test_chunk_time_window_total_lines():
    result = chunk(LINES, window=timedelta(seconds=2))
    assert result.total_lines == len(LINES)


def test_chunk_time_window_splits_correctly():
    # lines at 0,1,2,3,4 seconds; window=2s → [0,1], [2,3], [4]
    result = chunk(LINES, window=timedelta(seconds=2))
    assert result.chunk_count == 3


def test_chunk_raises_if_both_args():
    with pytest.raises(ValueError):
        chunk(LINES, chunk_size=2, window=timedelta(seconds=1))


def test_chunk_raises_if_neither_arg():
    with pytest.raises(ValueError):
        chunk(LINES)


def test_chunk_size_zero_raises():
    with pytest.raises(ValueError):
        chunk(LINES, chunk_size=0)


def test_chunk_negative_window_raises():
    with pytest.raises(ValueError):
        chunk(LINES, window=timedelta(seconds=-1))
