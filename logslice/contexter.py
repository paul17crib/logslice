"""Context extractor – returns lines surrounding each matching line."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Tuple
from collections import deque


@dataclass
class ContextResult:
    """Result returned by :func:`extract_context`."""
    lines: List[Tuple[int, str]]   # (1-based line number, text)
    total_input: int
    match_count: int
    context_lines: int

    @property
    def total_output(self) -> int:  # noqa: D401
        """Number of lines in the output."""
        return len(self.lines)


def _matches(line: str, keyword: str, *, case_sensitive: bool) -> bool:
    if case_sensitive:
        return keyword in line
    return keyword.lower() in line.lower()


def extract_context(
    lines: Iterable[str],
    keyword: str,
    *,
    before: int = 2,
    after: int = 2,
    case_sensitive: bool = False,
) -> ContextResult:
    """Extract lines that contain *keyword* together with surrounding context.

    Parameters
    ----------
    lines:
        Iterable of raw log lines.
    keyword:
        The string to search for.
    before:
        Number of lines to include *before* each match.
    after:
        Number of lines to include *after* each match.
    case_sensitive:
        Whether the keyword match is case-sensitive.
    """
    if before < 0 or after < 0:
        raise ValueError("'before' and 'after' must be non-negative")

    all_lines: List[str] = list(lines)
    total_input = len(all_lines)
    match_count = 0

    # Collect indices of matching lines.
    match_indices = [
        i for i, ln in enumerate(all_lines)
        if _matches(ln, keyword, case_sensitive=case_sensitive)
    ]
    match_count = len(match_indices)

    # Expand each match to a window and merge overlapping windows.
    included: set[int] = set()
    for idx in match_indices:
        start = max(0, idx - before)
        end = min(total_input - 1, idx + after)
        for j in range(start, end + 1):
            included.add(j)

    result_lines = [
        (i + 1, all_lines[i]) for i in sorted(included)
    ]

    return ContextResult(
        lines=result_lines,
        total_input=total_input,
        match_count=match_count,
        context_lines=before + after,
    )
