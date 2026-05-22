"""Accelerated log slicer that uses a :class:`LogIndex` for large files."""

from __future__ import annotations

from datetime import datetime
from typing import Iterator, Optional

from logslice.indexer import LogIndex, build_index, seek_to_offset
from logslice.parser import parse_timestamp

# Threshold (bytes) above which we build an index before slicing.
_INDEX_THRESHOLD = 10 * 1024 * 1024  # 10 MB


def _iter_lines_from(
    path: str, byte_offset: int
) -> Iterator[str]:
    """Yield decoded lines starting from *byte_offset*."""
    with open(path, "rb") as fh:
        fh.seek(byte_offset)
        # Discard the (potentially partial) first line when not at start.
        if byte_offset != 0:
            fh.readline()
        for raw in fh:
            yield raw.decode("utf-8", errors="replace")


def fast_slice(
    path: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    index: Optional[LogIndex] = None,
) -> Iterator[str]:
    """Yield log lines whose timestamps fall within [*start*, *end*].

    If *index* is not provided and the file exceeds :data:`_INDEX_THRESHOLD`
    bytes, one is built automatically.

    Continuation lines (lines without a parseable timestamp) are emitted
    together with the preceding timestamped line.
    """
    import os

    byte_offset = 0

    if start is not None:
        if index is None and os.path.getsize(path) >= _INDEX_THRESHOLD:
            index = build_index(path)
        if index is not None:
            byte_offset = seek_to_offset(index, start)

    in_range = start is None
    last_ts: Optional[datetime] = None

    for line in _iter_lines_from(path, byte_offset):
        ts = parse_timestamp(line)

        if ts is not None:
            last_ts = ts
            if end is not None and ts > end:
                break
            if start is not None and ts < start:
                in_range = False
                continue
            in_range = True

        if in_range:
            yield line


def fast_slice_with_index(
    path: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    sample_every: int = 500,
) -> Iterator[str]:
    """Convenience wrapper that always builds an index before slicing."""
    index = build_index(path, sample_every=sample_every)
    yield from fast_slice(path, start=start, end=end, index=index)
