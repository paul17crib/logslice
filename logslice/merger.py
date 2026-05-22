"""Merge and interleave multiple log slices in chronological order."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional, Tuple

from logslice.parser import parse_timestamp


@dataclass(order=True)
class _Entry:
    """Heap entry wrapping a log line with its parsed timestamp."""

    sort_key: Tuple  # (timestamp_or_max, source_index, line_number)
    line: str = field(compare=False)
    source: str = field(compare=False)


def _make_sort_key(ts, source_index: int, line_number: int) -> Tuple:
    """Build a stable sort key; lines without timestamps sort last."""
    if ts is None:
        # Use a sentinel that sorts after any real datetime
        return (1, source_index, line_number)
    return (0, ts, source_index, line_number)


def merge_logs(
    sources: List[Tuple[str, Iterable[str]]],
    tag: bool = False,
) -> Iterator[str]:
    """Merge multiple log line iterables into a single chronological stream.

    Parameters
    ----------
    sources:
        List of ``(label, lines)`` pairs.  *label* is used when *tag* is True.
    tag:
        When True, prefix each output line with ``[label] ``.

    Yields
    ------
    str
        Merged log lines in ascending timestamp order.  Lines that share the
        same timestamp are emitted in source-index order (stable merge).
    """
    heap: List[_Entry] = []
    iterators = []

    for source_index, (label, lines) in enumerate(sources):
        it = iter(lines)
        iterators.append((label, it))
        try:
            line = next(it)
            ts = parse_timestamp(line)
            key = _make_sort_key(ts, source_index, 0)
            heapq.heappush(heap, _Entry(sort_key=key, line=line, source=label))
        except StopIteration:
            pass

    line_counters = [0] * len(sources)

    while heap:
        entry = heapq.heappop(heap)
        # Identify which source this came from by matching the label
        source_index = next(
            i for i, (lbl, _) in enumerate(iterators) if lbl == entry.source
        )
        output = f"[{entry.source}] {entry.line}" if tag else entry.line
        yield output

        label, it = iterators[source_index]
        try:
            line = next(it)
            line_counters[source_index] += 1
            ts = parse_timestamp(line)
            key = _make_sort_key(ts, source_index, line_counters[source_index])
            heapq.heappush(heap, _Entry(sort_key=key, line=line, source=label))
        except StopIteration:
            pass
