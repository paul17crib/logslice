"""Log file profiler: analyses timestamp density, line rate, and gap detection."""

from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta
from typing import Iterable, List, Optional, Tuple

from logslice.parser import parse_timestamp


@dataclasses.dataclass
class GapInfo:
    """A detected gap between consecutive timestamped lines."""
    start: datetime
    end: datetime
    duration_seconds: float


@dataclasses.dataclass
class ProfileResult:
    total_lines: int
    timestamped_lines: int
    first_timestamp: Optional[datetime]
    last_timestamp: Optional[datetime]
    duration_seconds: Optional[float]
    lines_per_second: Optional[float]
    gaps: List[GapInfo]

    @property
    def coverage_ratio(self) -> float:
        """Fraction of lines that carry a parseable timestamp."""
        if self.total_lines == 0:
            return 0.0
        return self.timestamped_lines / self.total_lines


def _gap_threshold(duration_seconds: Optional[float]) -> float:
    """Return a gap threshold (seconds) adaptive to overall log duration."""
    if duration_seconds is None or duration_seconds <= 0:
        return 60.0
    # Flag gaps that are at least 5 % of total duration, minimum 10 s.
    return max(10.0, duration_seconds * 0.05)


def profile(
    lines: Iterable[str],
    gap_threshold_seconds: Optional[float] = None,
) -> ProfileResult:
    """Profile *lines* and return a :class:`ProfileResult`.

    Parameters
    ----------
    lines:
        Iterable of raw log lines.
    gap_threshold_seconds:
        Minimum gap length (seconds) to record.  When *None* an adaptive
        threshold is derived from the overall log duration.
    """
    total = 0
    timestamped = 0
    first_ts: Optional[datetime] = None
    last_ts: Optional[datetime] = None
    prev_ts: Optional[datetime] = None
    raw_gaps: List[Tuple[datetime, datetime]] = []

    for line in lines:
        total += 1
        ts = parse_timestamp(line)
        if ts is None:
            continue
        timestamped += 1
        if first_ts is None:
            first_ts = ts
        if prev_ts is not None and ts >= prev_ts:
            raw_gaps.append((prev_ts, ts))
        prev_ts = ts
        last_ts = ts

    duration: Optional[float] = None
    if first_ts is not None and last_ts is not None:
        duration = (last_ts - first_ts).total_seconds()

    threshold = (
        gap_threshold_seconds
        if gap_threshold_seconds is not None
        else _gap_threshold(duration)
    )

    gaps = [
        GapInfo(start=s, end=e, duration_seconds=(e - s).total_seconds())
        for s, e in raw_gaps
        if (e - s).total_seconds() >= threshold
    ]

    lps: Optional[float] = None
    if duration and duration > 0 and timestamped > 0:
        lps = timestamped / duration

    return ProfileResult(
        total_lines=total,
        timestamped_lines=timestamped,
        first_timestamp=first_ts,
        last_timestamp=last_ts,
        duration_seconds=duration,
        lines_per_second=lps,
        gaps=gaps,
    )
