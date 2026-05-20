"""Statistics and summary reporting for log slices."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator, Optional


@dataclass
class SliceStats:
    """Holds statistics collected during a log slice operation."""

    total_lines: int = 0
    matched_lines: int = 0
    continuation_lines: int = 0
    first_timestamp: Optional[datetime] = None
    last_timestamp: Optional[datetime] = None
    skipped_lines: int = 0

    @property
    def duration_seconds(self) -> Optional[float]:
        """Return the time span covered by matched entries in seconds."""
        if self.first_timestamp and self.last_timestamp:
            return (self.last_timestamp - self.first_timestamp).total_seconds()
        return None

    def to_dict(self) -> dict:
        """Serialise stats to a plain dictionary."""
        return {
            "total_lines": self.total_lines,
            "matched_lines": self.matched_lines,
            "continuation_lines": self.continuation_lines,
            "skipped_lines": self.skipped_lines,
            "first_timestamp": self.first_timestamp.isoformat() if self.first_timestamp else None,
            "last_timestamp": self.last_timestamp.isoformat() if self.last_timestamp else None,
            "duration_seconds": self.duration_seconds,
        }


def collect_stats(lines: Iterator[str], parse_ts) -> tuple[list[str], SliceStats]:
    """Consume *lines* and build a :class:`SliceStats` alongside the collected output.

    Parameters
    ----------
    lines:
        Iterator of log lines already filtered by :func:`~logslice.slicer.slice_log`.
    parse_ts:
        Callable that accepts a raw line and returns a :class:`datetime` or ``None``.

    Returns
    -------
    tuple[list[str], SliceStats]
        The collected lines and the computed statistics.
    """
    stats = SliceStats()
    collected: list[str] = []

    for line in lines:
        stats.total_lines += 1
        collected.append(line)
        ts = parse_ts(line)
        if ts is not None:
            stats.matched_lines += 1
            if stats.first_timestamp is None:
                stats.first_timestamp = ts
            stats.last_timestamp = ts
        else:
            stats.continuation_lines += 1

    return collected, stats
