"""Render a SummaryResult as human-readable text or JSON."""
from __future__ import annotations

import json
from typing import Callable

from logslice.summarizer import SummaryResult


def report_summary_text(result: SummaryResult) -> str:
    """Return a multi-line human-readable summary string."""
    lines = [
        f"Total lines   : {result.total_lines}",
        f"Unique lines  : {result.unique_line_count}",
        f"First entry   : {result.first_timestamp or 'n/a'}",
        f"Last entry    : {result.last_timestamp or 'n/a'}",
        "Severity counts:",
    ]
    for sev, count in sorted(result.severity_counts.items()):
        lines.append(f"  {sev:<10}: {count}")
    if result.top_errors:
        lines.append("Top errors:")
        for i, err in enumerate(result.top_errors, 1):
            lines.append(f"  {i}. {err}")
    return "\n".join(lines)


def report_summary_json(result: SummaryResult) -> str:
    """Return a JSON-encoded summary string."""
    payload = {
        "total_lines": result.total_lines,
        "unique_line_count": result.unique_line_count,
        "first_timestamp": result.first_timestamp,
        "last_timestamp": result.last_timestamp,
        "severity_counts": result.severity_counts,
        "top_errors": result.top_errors,
    }
    return json.dumps(payload, indent=2)


def get_summary_reporter(fmt: str) -> Callable[[SummaryResult], str]:
    """Return the reporter callable for *fmt* ('text' or 'json')."""
    reporters = {
        "text": report_summary_text,
        "json": report_summary_json,
    }
    if fmt not in reporters:
        raise ValueError(f"Unknown summary format {fmt!r}; choose from {list(reporters)}")
    return reporters[fmt]
