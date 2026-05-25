"""Aggregator: group log lines into time-window buckets and compute counts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional

from logslice.parser import parse_timestamp


@dataclass
class AggregateWindow:
    """A single time-window bucket with its line count and sample lines."""

    label: str
    start: datetime
    end: datetime
    count: int = 0
    lines: List[str] = field(default_factory=list)

    @property
    def size(self) -> int:  # alias kept for consistency with other modules
        return self.count


@dataclass
class AggregateResult:
    """Result returned by :func:`aggregate`."""

    windows: List[AggregateWindow]
    total_lines: int
    ungrouped: int  # lines without a parseable timestamp
    window_seconds: int

    @property
    def window_count(self) -> int:
        return len(self.windows)

    @property
    def peak_window(self) -> Optional[AggregateWindow]:
        """Window with the highest line count, or *None* if no windows."""
        if not self.windows:
            return None
        return max(self.windows, key=lambda w: w.count)


def _floor_to_window(ts: datetime, seconds: int) -> datetime:
    """Truncate *ts* to the nearest multiple of *seconds* since the epoch."""
    epoch = datetime(1970, 1, 1, tzinfo=ts.tzinfo)
    delta = int((ts - epoch).total_seconds())
    floored = delta - (delta % seconds)
    return epoch + timedelta(seconds=floored)


def aggregate(
    lines: Iterable[str],
    window_seconds: int = 60,
    max_samples: int = 5,
) -> AggregateResult:
    """Aggregate *lines* into fixed-width time windows.

    Parameters
    ----------
    lines:
        Iterable of raw log lines.
    window_seconds:
        Width of each bucket in seconds (default 60).
    max_samples:
        Maximum number of sample lines stored per window.

    Returns
    -------
    AggregateResult
    """
    if window_seconds < 1:
        raise ValueError("window_seconds must be >= 1")

    buckets: Dict[datetime, AggregateWindow] = {}
    total = 0
    ungrouped = 0

    for line in lines:
        total += 1
        ts = parse_timestamp(line)
        if ts is None:
            ungrouped += 1
            continue
        key = _floor_to_window(ts, window_seconds)
        if key not in buckets:
            label = key.strftime("%Y-%m-%dT%H:%M:%S")
            buckets[key] = AggregateWindow(
                label=label,
                start=key,
                end=key + timedelta(seconds=window_seconds),
            )
        w = buckets[key]
        w.count += 1
        if len(w.lines) < max_samples:
            w.lines.append(line)

    windows = [buckets[k] for k in sorted(buckets)]
    return AggregateResult(
        windows=windows,
        total_lines=total,
        ungrouped=ungrouped,
        window_seconds=window_seconds,
    )
