"""Pattern-based line matcher for logslice.

Provides flexible matching of log lines against one or more regex or
literal patterns, returning structured results with match metadata.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence


@dataclass
class MatchedLine:
    line: str
    line_number: int
    pattern: str
    span: tuple  # (start, end) of first match

    @property
    def is_match(self) -> bool:
        return True


@dataclass
class MatchResult:
    lines: List[MatchedLine]
    total_input: int
    pattern_counts: dict  # pattern -> number of lines matched

    @property
    def match_count(self) -> int:
        return len(self.lines)

    @property
    def match_ratio(self) -> float:
        if self.total_input == 0:
            return 0.0
        return self.match_count / self.total_input


def _compile_patterns(
    patterns: Sequence[str],
    case_sensitive: bool = False,
) -> List[re.Pattern]:
    flags = 0 if case_sensitive else re.IGNORECASE
    compiled = []
    for p in patterns:
        try:
            compiled.append(re.compile(p, flags))
        except re.error as exc:
            raise ValueError(f"Invalid pattern {p!r}: {exc}") from exc
    return compiled


def match_lines(
    lines: Iterable[str],
    patterns: Sequence[str],
    *,
    case_sensitive: bool = False,
    match_all: bool = False,
) -> MatchResult:
    """Match *lines* against *patterns*.

    Parameters
    ----------
    lines:
        Iterable of raw log lines.
    patterns:
        One or more regex patterns to match against.
    case_sensitive:
        When ``True`` matching is case-sensitive (default: ``False``).
    match_all:
        When ``True`` a line must match ALL patterns to be included;
        otherwise any single match suffices (OR logic).
    """
    if not patterns:
        raise ValueError("At least one pattern is required.")

    compiled = _compile_patterns(patterns, case_sensitive=case_sensitive)
    pattern_counts: dict = {p: 0 for p in patterns}
    matched: List[MatchedLine] = []
    total = 0

    for lineno, line in enumerate(lines, start=1):
        total += 1
        hits = []
        for raw_p, rx in zip(patterns, compiled):
            m = rx.search(line)
            if m:
                hits.append((raw_p, m))

        include = (len(hits) == len(patterns)) if match_all else bool(hits)
        if include and hits:
            raw_p, m = hits[0]
            matched.append(
                MatchedLine(
                    line=line,
                    line_number=lineno,
                    pattern=raw_p,
                    span=m.span(),
                )
            )
            for rp, _ in hits:
                pattern_counts[rp] += 1

    return MatchResult(
        lines=matched,
        total_input=total,
        pattern_counts=pattern_counts,
    )
