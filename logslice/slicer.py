"""Core log slicing logic: extracts lines within a given time range."""

import os
from datetime import datetime
from typing import Iterator, Optional, Tuple

from logslice.parser import parse_timestamp

DEFAULT_CHUNK_SIZE = 8192


def _iter_lines(filepath: str, encoding: str = 'utf-8') -> Iterator[str]:
    """Yield lines from a file, handling encoding errors gracefully."""
    with open(filepath, 'r', encoding=encoding, errors='replace') as fh:
        for line in fh:
            yield line.rstrip('\n')


def slice_log(
    filepath: str,
    start: datetime,
    end: datetime,
    encoding: str = 'utf-8',
) -> Iterator[str]:
    """Yield log lines whose timestamps fall within [start, end].

    Lines without a detectable timestamp are included if they appear
    between two lines that are within the range (continuation lines).

    Args:
        filepath: Path to the log file.
        start: Inclusive start datetime.
        end: Inclusive end datetime.
        encoding: File encoding.

    Yields:
        Log lines within the specified time range.
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"Log file not found: {filepath}")

    if start > end:
        raise ValueError(f"start ({start}) must be <= end ({end})")

    in_range = False
    pending_continuation: list = []

    for line in _iter_lines(filepath, encoding=encoding):
        ts = parse_timestamp(line)

        if ts is None:
            # Continuation line — buffer it; emit only if we're in range
            if in_range:
                yield line
            else:
                pending_continuation.append(line)
            continue

        # We have a timestamped line
        if start <= ts <= end:
            # Flush any buffered continuation lines that preceded this
            if not in_range:
                for cont in pending_continuation:
                    yield cont
            pending_continuation.clear()
            in_range = True
            yield line
        else:
            pending_continuation.clear()
            in_range = False
            if ts > end:
                # Past the range — stop processing
                return


def count_lines(
    filepath: str,
    start: datetime,
    end: datetime,
    encoding: str = 'utf-8',
) -> Tuple[int, Optional[datetime], Optional[datetime]]:
    """Count matching lines and return first/last timestamps found."""
    count = 0
    first_ts: Optional[datetime] = None
    last_ts: Optional[datetime] = None

    for line in slice_log(filepath, start, end, encoding=encoding):
        count += 1
        ts = parse_timestamp(line)
        if ts:
            if first_ts is None:
                first_ts = ts
            last_ts = ts

    return count, first_ts, last_ts
