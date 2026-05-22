"""Human-readable and machine-readable stats reporters."""

from __future__ import annotations

import json
import sys
from typing import IO, Literal

from logslice.stats import SliceStats

ReportFormat = Literal["text", "json"]

VALID_FORMATS = ("text", "json")


def report_text(stats: SliceStats, file: IO[str] = sys.stderr) -> None:
    """Write a brief human-readable summary to *file* (default: stderr)."""
    lines = [
        "--- logslice stats ---",
        f"  Total lines     : {stats.total_lines}",
        f"  Matched lines   : {stats.matched_lines}",
        f"  Continuation    : {stats.continuation_lines}",
        f"  Skipped lines   : {stats.skipped_lines}",
    ]
    if stats.first_timestamp:
        lines.append(f"  First timestamp : {stats.first_timestamp.isoformat()}")  # noqa: E501
    if stats.last_timestamp:
        lines.append(f"  Last timestamp  : {stats.last_timestamp.isoformat()}")
    if stats.duration_seconds is not None:
        lines.append(f"  Duration        : {stats.duration_seconds:.3f}s")
    lines.append("----------------------")
    print("\n".join(lines), file=file)


def report_json(stats: SliceStats, file: IO[str] = sys.stderr) -> None:
    """Write a JSON object with stats to *file* (default: stderr)."""
    print(json.dumps(stats.to_dict(), indent=2), file=file)


def get_reporter(fmt: ReportFormat):
    """Return the reporter callable for the given format string.

    Parameters
    ----------
    fmt:
        Output format; must be one of ``'text'`` or ``'json'``.

    Raises
    ------
    ValueError
        If *fmt* is not a recognised format string.
    """
    if fmt == "json":
        return report_json
    if fmt == "text":
        return report_text
    raise ValueError(
        f"Unknown report format: {fmt!r}. Choose one of: {', '.join(repr(f) for f in VALID_FORMATS)}."
    )
