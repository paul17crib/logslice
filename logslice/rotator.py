"""Log rotation detector: identifies and orders rotated log file segments."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class RotatedSegment:
    """A single log file segment, possibly rotated."""
    path: Path
    index: int          # 0 = current, 1 = most recent rotation, etc.
    size: int
    mtime: float


@dataclass
class RotationResult:
    """Result of scanning for rotated log segments."""
    base: Path
    segments: List[RotatedSegment] = field(default_factory=list)

    @property
    def total_size(self) -> int:
        return sum(s.size for s in self.segments)

    @property
    def count(self) -> int:
        return len(self.segments)


# Patterns like app.log, app.log.1, app.log.2, app.log.1.gz
_ROTATION_RE = re.compile(r"^(?P<base>.+?\.log)(?:\.(?P<idx>\d+))?(?:\.gz)?$")


def _rotation_index(path: Path, base_name: str) -> Optional[int]:
    """Return the numeric rotation index for *path* relative to *base_name*.

    Returns 0 for the base file, a positive integer for rotated copies, or
    None if the file does not belong to this log family.
    """
    name = path.name
    if name == base_name:
        return 0
    m = _ROTATION_RE.match(name)
    if m and m.group("base") == base_name and m.group("idx") is not None:
        return int(m.group("idx"))
    return None


def find_rotated_segments(
    log_path: str | Path,
    *,
    max_segments: int = 20,
) -> RotationResult:
    """Discover rotated segments for *log_path* in the same directory.

    Segments are returned ordered from oldest (highest index) to newest (index
    0 = current file), so callers can iterate in chronological order.

    Parameters
    ----------
    log_path:
        Path to the *current* (active) log file.
    max_segments:
        Upper limit on the number of segments to return (including the current
        file).  Segments beyond this limit are silently ignored.
    """
    log_path = Path(log_path)
    directory = log_path.parent
    base_name = log_path.name

    result = RotationResult(base=log_path)

    try:
        entries = list(directory.iterdir())
    except OSError:
        return result

    segments: List[RotatedSegment] = []
    for entry in entries:
        if not entry.is_file():
            continue
        idx = _rotation_index(entry, base_name)
        if idx is None:
            continue
        try:
            st = entry.stat()
        except OSError:
            continue
        segments.append(RotatedSegment(
            path=entry,
            index=idx,
            size=st.st_size,
            mtime=st.st_mtime,
        ))

    # Sort: highest index first (oldest), then reverse so oldest comes first
    segments.sort(key=lambda s: s.index, reverse=True)
    result.segments = segments[:max_segments]
    return result
