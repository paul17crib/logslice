"""Deduplicator: remove or count duplicate lines in a log stream."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator


@dataclass
class DedupeResult:
    """Holds deduplicated lines and statistics."""

    lines: list[str]
    total_input: int
    duplicate_count: int
    unique_count: int


def deduplicate(
    lines: Iterable[str],
    *,
    consecutive_only: bool = False,
    keep: str = "first",
) -> DedupeResult:
    """Remove duplicate lines from *lines*.

    Parameters
    ----------
    lines:
        Input iterable of log lines.
    consecutive_only:
        When *True*, only collapse adjacent identical lines (run-length
        deduplication).  When *False* (default), remove all duplicates
        regardless of position.
    keep:
        ``"first"`` (default) keeps the first occurrence; ``"last"`` keeps
        the last occurrence (only meaningful when *consecutive_only* is
        ``False``).
    """
    if keep not in ("first", "last"):
        raise ValueError("keep must be 'first' or 'last'")

    total_input = 0
    duplicate_count = 0
    output: list[str] = []

    if consecutive_only:
        prev: str | None = None
        for line in lines:
            total_input += 1
            if line == prev:
                duplicate_count += 1
            else:
                output.append(line)
                prev = line
    else:
        seen: dict[str, int] = {}  # line -> first index in output
        for line in lines:
            total_input += 1
            if line in seen:
                duplicate_count += 1
                if keep == "last":
                    # Move to end: remove old position, append new
                    output.pop(seen[line])
                    # Reindex all entries after the removed position
                    removed_idx = seen[line]
                    for k, v in seen.items():
                        if v > removed_idx:
                            seen[k] = v - 1
                    seen[line] = len(output)
                    output.append(line)
            else:
                seen[line] = len(output)
                output.append(line)

    return DedupeResult(
        lines=output,
        total_input=total_input,
        duplicate_count=duplicate_count,
        unique_count=len(output),
    )


def iter_deduplicated(
    lines: Iterable[str],
    *,
    consecutive_only: bool = True,
) -> Iterator[str]:
    """Streaming deduplication (consecutive only) — yields unique lines."""
    prev: str | None = None
    for line in lines:
        if line != prev:
            yield line
            prev = line
