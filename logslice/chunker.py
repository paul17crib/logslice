"""Split a sequence of log lines into fixed-size or time-windowed chunks."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Iterator, List, Optional, Sequence

from logslice.parser import parse_timestamp


@dataclass
class Chunk:
    index: int
    lines: List[str] = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.lines)


@dataclass
class ChunkResult:
    chunks: List[Chunk]
    total_lines: int
    chunk_count: int


def _iter_chunks_by_size(lines: Sequence[str], chunk_size: int) -> Iterator[Chunk]:
    """Yield Chunk objects of at most *chunk_size* lines each."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be >= 1")
    buf: List[str] = []
    idx = 0
    for line in lines:
        buf.append(line)
        if len(buf) >= chunk_size:
            yield Chunk(index=idx, lines=buf)
            buf = []
            idx += 1
    if buf:
        yield Chunk(index=idx, lines=buf)


def _iter_chunks_by_time(lines: Sequence[str], window: timedelta) -> Iterator[Chunk]:
    """Yield Chunk objects grouped by *window*-sized time buckets."""
    if window.total_seconds() <= 0:
        raise ValueError("window must be a positive timedelta")
    buf: List[str] = []
    bucket_start = None
    idx = 0
    for line in lines:
        ts = parse_timestamp(line)
        if ts is not None and bucket_start is None:
            bucket_start = ts
        if ts is not None and bucket_start is not None and (ts - bucket_start) >= window:
            if buf:
                yield Chunk(index=idx, lines=buf)
                idx += 1
            buf = []
            bucket_start = ts
        buf.append(line)
    if buf:
        yield Chunk(index=idx, lines=buf)


def chunk(
    lines: Sequence[str],
    chunk_size: Optional[int] = None,
    window: Optional[timedelta] = None,
) -> ChunkResult:
    """Chunk *lines* by size or time window.

    Exactly one of *chunk_size* or *window* must be provided.
    """
    if (chunk_size is None) == (window is None):
        raise ValueError("Provide exactly one of chunk_size or window")
    if chunk_size is not None:
        chunks = list(_iter_chunks_by_size(lines, chunk_size))
    else:
        chunks = list(_iter_chunks_by_time(lines, window))  # type: ignore[arg-type]
    total = sum(c.size for c in chunks)
    return ChunkResult(chunks=chunks, total_lines=total, chunk_count=len(chunks))
