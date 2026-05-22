"""Tail utilities: follow a log file in real-time or return the last N lines."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Generator, Iterable, List, Optional

from logslice.parser import parse_timestamp


@dataclass
class TailResult:
    lines: List[str] = field(default_factory=list)
    total_read: int = 0


def tail_lines(path: str, n: int = 20) -> TailResult:
    """Return the last *n* lines from *path* without reading the whole file."""
    if n <= 0:
        return TailResult(lines=[], total_read=0)

    chunk_size = 8192
    collected: List[str] = []
    total_read = 0

    with open(path, "rb") as fh:
        fh.seek(0, os.SEEK_END)
        file_size = fh.tell()
        remaining = file_size
        buf = b""

        while remaining > 0 and len(collected) <= n:
            read_size = min(chunk_size, remaining)
            remaining -= read_size
            fh.seek(remaining)
            chunk = fh.read(read_size)
            total_read += len(chunk)
            buf = chunk + buf
            collected = buf.decode("utf-8", errors="replace").splitlines()

    lines = collected[-n:] if len(collected) >= n else collected
    return TailResult(lines=lines, total_read=total_read)


def follow(
    path: str,
    poll_interval: float = 0.25,
    start_from_end: bool = True,
    start_ts: Optional[str] = None,
    timeout: Optional[float] = None,
) -> Generator[str, None, None]:
    """Yield new lines appended to *path*, similar to ``tail -f``.

    Parameters
    ----------
    path:            Path to the log file.
    poll_interval:   Seconds between file-size checks.
    start_from_end:  If True, skip existing content and only yield new lines.
    start_ts:        If given, only yield lines whose timestamp >= this value.
    timeout:         Stop following after this many seconds (None = forever).
    """
    filter_dt = parse_timestamp(start_ts) if start_ts else None
    deadline = (time.monotonic() + timeout) if timeout is not None else None

    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        if start_from_end:
            fh.seek(0, os.SEEK_END)

        while True:
            if deadline is not None and time.monotonic() >= deadline:
                break

            line = fh.readline()
            if not line:
                time.sleep(poll_interval)
                continue

            line = line.rstrip("\n")
            if filter_dt is not None:
                ts = parse_timestamp(line)
                if ts is not None and ts < filter_dt:
                    continue

            yield line
