"""Severity-based filtering: keep or reject lines by their classified severity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional

from logslice.classifier import ClassifiedLine, SEVERITY_ORDER, iter_classified


@dataclass
class FilterResult:
    lines: List[str] = field(default_factory=list)
    total_input: int = 0
    kept: int = 0

    @property
    def rejected(self) -> int:
        return self.total_input - self.kept


def _severity_index(level: str) -> int:
    try:
        return SEVERITY_ORDER.index(level.upper())
    except ValueError:
        raise ValueError(f"Unknown severity level: {level!r}. Choose from {SEVERITY_ORDER}")


def iter_filter_by_severity(
    lines: Iterable[str],
    min_level: Optional[str] = None,
    max_level: Optional[str] = None,
    include_unclassified: bool = True,
) -> Iterator[str]:
    """Yield lines whose severity falls within [min_level, max_level]."""
    min_idx = _severity_index(min_level) if min_level else 0
    max_idx = _severity_index(max_level) if max_level else len(SEVERITY_ORDER) - 1

    for cl in iter_classified(lines):
        if cl.severity is None:
            if include_unclassified:
                yield cl.line
        else:
            idx = _severity_index(cl.severity)
            if min_idx <= idx <= max_idx:
                yield cl.line


def filter_by_severity(
    lines: Iterable[str],
    min_level: Optional[str] = None,
    max_level: Optional[str] = None,
    include_unclassified: bool = True,
) -> FilterResult:
    result = FilterResult()
    for line in lines:
        result.total_input += 1
    # Re-iterate (materialise if needed)
    lines_list = list(lines) if not isinstance(lines, list) else lines
    result.total_input = len(lines_list)
    for kept_line in iter_filter_by_severity(
        lines_list,
        min_level=min_level,
        max_level=max_level,
        include_unclassified=include_unclassified,
    ):
        result.lines.append(kept_line)
        result.kept += 1
    return result
