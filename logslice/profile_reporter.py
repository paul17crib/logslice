"""Human-readable and JSON reporters for :class:`ProfileResult`."""

from __future__ import annotations

import json
from typing import Callable

from logslice.profiler import ProfileResult


def report_profile_text(result: ProfileResult) -> str:
    """Return a multi-line text summary of *result*."""
    lines = [
        f"Total lines      : {result.total_lines}",
        f"Timestamped lines: {result.timestamped_lines} "
        f"({result.coverage_ratio:.1%} coverage)",
    ]
    if result.first_timestamp:
        lines.append(f"First timestamp  : {result.first_timestamp.isoformat()}") 
    if result.last_timestamp:
        lines.append(f"Last timestamp   : {result.last_timestamp.isoformat()}")
    if result.duration_seconds is not None:
        lines.append(f"Duration         : {result.duration_seconds:.2f}s")
    if result.lines_per_second is not None:
        lines.append(f"Lines / second   : {result.lines_per_second:.4f}")
    if result.gaps:
        lines.append(f"Gaps detected    : {len(result.gaps)}")
        for i, gap in enumerate(result.gaps, 1):
            lines.append(
                f"  Gap {i}: {gap.start.isoformat()} -> {gap.end.isoformat()} "
                f"({gap.duration_seconds:.1f}s)"
            )
    else:
        lines.append("Gaps detected    : 0")
    return "\n".join(lines)


def report_profile_json(result: ProfileResult) -> str:
    """Return a JSON string representation of *result*."""
    def _iso(dt):
        return dt.isoformat() if dt is not None else None

    payload = {
        "total_lines": result.total_lines,
        "timestamped_lines": result.timestamped_lines,
        "coverage_ratio": round(result.coverage_ratio, 6),
        "first_timestamp": _iso(result.first_timestamp),
        "last_timestamp": _iso(result.last_timestamp),
        "duration_seconds": result.duration_seconds,
        "lines_per_second": result.lines_per_second,
        "gaps": [
            {
                "start": _iso(g.start),
                "end": _iso(g.end),
                "duration_seconds": g.duration_seconds,
            }
            for g in result.gaps
        ],
    }
    return json.dumps(payload, indent=2)


def get_profile_reporter(fmt: str = "text") -> Callable[[ProfileResult], str]:
    """Return a reporter callable for *fmt* (``'text'`` or ``'json'``)."""
    reporters = {
        "text": report_profile_text,
        "json": report_profile_json,
    }
    if fmt not in reporters:
        raise ValueError(f"Unknown format {fmt!r}. Choose from: {list(reporters)}")
    return reporters[fmt]
