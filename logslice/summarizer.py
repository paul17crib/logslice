"""Summarizer: produce a concise summary of a log slice."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from logslice.classifier import ClassifiedLine, classify
from logslice.parser import parse_timestamp


@dataclass
class SummaryResult:
    total_lines: int
    first_timestamp: Optional[str]
    last_timestamp: Optional[str]
    severity_counts: dict
    top_errors: List[str]
    unique_line_count: int


def _is_classified(line: object) -> bool:
    return isinstance(line, ClassifiedLine)


def summarize(
    lines: Iterable[str],
    *,
    top_n: int = 5,
    error_severities: tuple = ("ERROR", "CRITICAL"),
) -> SummaryResult:
    """Summarise *lines*, returning counts and top error messages."""
    all_lines: List[str] = list(lines)
    total = len(all_lines)

    first_ts: Optional[str] = None
    last_ts: Optional[str] = None
    for raw in all_lines:
        ts = parse_timestamp(raw)
        if ts is not None:
            if first_ts is None:
                first_ts = raw[:32].strip()
            last_ts = raw[:32].strip()

    classified = classify(all_lines)
    sev_counts = dict(classified.counts_by_severity())

    error_lines: List[str] = [
        cl.line
        for cl in classified.lines
        if _is_classified(cl) and cl.severity in error_severities  # type: ignore[union-attr]
    ]

    seen: dict = {}
    for ln in error_lines:
        seen[ln.strip()] = seen.get(ln.strip(), 0) + 1
    top_errors = [
        k for k, _ in sorted(seen.items(), key=lambda kv: -kv[1])
    ][:top_n]

    unique_count = len({ln.strip() for ln in all_lines})

    return SummaryResult(
        total_lines=total,
        first_timestamp=first_ts,
        last_timestamp=last_ts,
        severity_counts=sev_counts,
        top_errors=top_errors,
        unique_line_count=unique_count,
    )
