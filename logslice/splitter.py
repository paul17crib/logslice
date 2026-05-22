"""logslice.splitter — Split a log file into multiple output files by time window."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Iterator, List, Optional

from logslice.parser import parse_timestamp


@dataclass
class SplitSegment:
    """Metadata for a single output segment produced by splitting."""
    path: str
    start: Optional[datetime]
    end: Optional[datetime]
    line_count: int


@dataclass
class SplitResult:
    """Aggregated result returned by :func:`split_by_window`."""
    segments: List[SplitSegment] = field(default_factory=list)

    @property
    def total_lines(self) -> int:
        return sum(s.line_count for s in self.segments)

    @property
    def segment_count(self) -> int:
        return len(self.segments)


def _window_key(ts: datetime, window: timedelta) -> int:
    """Return an integer bucket index for *ts* given *window* size."""
    epoch = datetime(ts.year, ts.month, ts.day, tzinfo=ts.tzinfo)
    return int((ts - epoch).total_seconds() // window.total_seconds())


def split_by_window(
    lines: Iterator[str],
    output_dir: str,
    window: timedelta,
    prefix: str = "segment",
    name_fn: Optional[Callable[[int, Optional[datetime]], str]] = None,
) -> SplitResult:
    """Split *lines* into separate files, one per *window* interval.

    Parameters
    ----------
    lines:
        Iterable of raw log lines (newlines are preserved if present).
    output_dir:
        Directory where segment files are written (created if absent).
    window:
        Duration of each segment bucket (e.g. ``timedelta(hours=1)``).
    prefix:
        Filename prefix used when *name_fn* is not supplied.
    name_fn:
        Optional callable ``(bucket_index, first_ts) -> filename`` for
        custom segment naming.  The extension ``.log`` is appended automatically.
    """
    os.makedirs(output_dir, exist_ok=True)

    result = SplitResult()
    current_bucket: Optional[int] = None
    current_file = None
    current_path: Optional[str] = None
    current_start: Optional[datetime] = None
    current_end: Optional[datetime] = None
    current_count = 0
    bucket_index = 0

    def _flush() -> None:
        nonlocal current_file, current_path, current_start, current_end, current_count
        if current_file is not None:
            current_file.close()
            result.segments.append(
                SplitSegment(
                    path=current_path,
                    start=current_start,
                    end=current_end,
                    line_count=current_count,
                )
            )
        current_file = None
        current_path = None
        current_start = None
        current_end = None
        current_count = 0

    for line in lines:
        ts = parse_timestamp(line)
        bucket = _window_key(ts, window) if ts is not None else current_bucket

        if bucket != current_bucket:
            _flush()
            current_bucket = bucket
            if name_fn is not None:
                fname = name_fn(bucket_index, ts) + ".log"
            else:
                tag = ts.strftime("%Y%m%dT%H%M%S") if ts else f"unknown_{bucket_index}"
                fname = f"{prefix}_{tag}.log"
            current_path = os.path.join(output_dir, fname)
            current_file = open(current_path, "w", encoding="utf-8")
            current_start = ts
            bucket_index += 1

        if current_file is None:
            # No timestamp ever seen — open a fallback segment
            current_bucket = 0
            fname = f"{prefix}_untimestamped.log"
            current_path = os.path.join(output_dir, fname)
            current_file = open(current_path, "w", encoding="utf-8")

        current_file.write(line if line.endswith("\n") else line + "\n")
        current_count += 1
        if ts is not None:
            current_end = ts

    _flush()
    return result
