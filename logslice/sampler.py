"""Line sampler: extract every N-th matched line from a log slice."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional

from logslice.parser import parse_timestamp


@dataclass
class SampleResult:
    """Holds the output of a sampling run."""

    lines: List[str] = field(default_factory=list)
    total_visited: int = 0
    total_sampled: int = 0


def sample_lines(
    lines: Iterable[str],
    step: int = 1,
    max_lines: Optional[int] = None,
) -> SampleResult:
    """Return every *step*-th line from *lines*, up to *max_lines* results.

    Args:
        lines:     Iterable of raw log lines (may include continuation lines).
        step:      Keep one line for every *step* lines visited (default 1 = keep all).
        max_lines: Stop after collecting this many lines (None = unlimited).

    Returns:
        A :class:`SampleResult` with the selected lines and counters.
    """
    if step < 1:
        raise ValueError(f"step must be >= 1, got {step}")

    result = SampleResult()
    counter = 0

    for line in lines:
        result.total_visited += 1
        if counter % step == 0:
            result.lines.append(line)
            result.total_sampled += 1
            if max_lines is not None and result.total_sampled >= max_lines:
                break
        counter += 1

    return result


def sample_by_timestamp(
    lines: Iterable[str],
    interval_seconds: float,
) -> Iterator[str]:
    """Yield lines whose timestamp is at least *interval_seconds* after the
    previously yielded timestamp-bearing line.

    Continuation lines (no parseable timestamp) are always attached to the
    most-recently yielded timestamped line and included automatically.
    """
    if interval_seconds < 0:
        raise ValueError("interval_seconds must be >= 0")

    last_ts = None
    pending_continuations: List[str] = []
    emit_pending = False

    for line in lines:
        ts = parse_timestamp(line)
        if ts is None:
            # continuation line — buffer it
            if emit_pending:
                pending_continuations.append(line)
            continue

        # Flush buffered continuations for the previous block
        yield from pending_continuations
        pending_continuations = []
        emit_pending = False

        if last_ts is None or (ts - last_ts).total_seconds() >= interval_seconds:
            last_ts = ts
            emit_pending = True
            yield line

    if emit_pending:
        yield from pending_continuations
