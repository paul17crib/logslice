"""Binary-search index for fast seeking in large log files."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple

from logslice.parser import parse_timestamp


@dataclass
class LogIndex:
    """Sparse index mapping byte offsets to parsed timestamps."""

    entries: List[Tuple[int, datetime]] = field(default_factory=list)
    """List of (byte_offset, timestamp) pairs, sorted by offset."""

    def __len__(self) -> int:
        return len(self.entries)

    def is_empty(self) -> bool:
        return len(self.entries) == 0


def build_index(path: str, sample_every: int = 500) -> LogIndex:
    """Build a sparse index by sampling every *sample_every* lines.

    Parameters
    ----------
    path:
        Path to the log file.
    sample_every:
        Record a byte-offset entry for every N-th line that carries a
        parseable timestamp.

    Returns
    -------
    LogIndex
        Sparse index that can be used with :func:`seek_to_offset`.
    """
    index = LogIndex()
    line_count = 0

    with open(path, "rb") as fh:
        offset = 0
        for raw in fh:
            line = raw.decode("utf-8", errors="replace")
            ts = parse_timestamp(line)
            if ts is not None:
                if line_count % sample_every == 0:
                    index.entries.append((offset, ts))
                line_count += 1
            offset += len(raw)

    return index


def seek_to_offset(index: LogIndex, target: datetime) -> int:
    """Return the best byte offset to start scanning for *target*.

    Uses binary search over the sparse index.  Returns 0 when the index
    is empty or *target* is before the first entry.
    """
    if index.is_empty():
        return 0

    lo, hi = 0, len(index.entries) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if index.entries[mid][1] <= target:
            lo = mid
        else:
            hi = mid - 1

    offset, ts = index.entries[lo]
    # Step back one entry to avoid missing lines right at the boundary.
    if ts > target and lo > 0:
        offset = index.entries[lo - 1][0]
    return offset


def index_file_size(path: str) -> int:
    """Return the size in bytes of *path* (convenience wrapper)."""
    return os.path.getsize(path)
