"""Line annotator — attaches metadata tags to log lines based on pattern rules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional, Tuple


@dataclass
class AnnotatedLine:
    """A log line paired with its matched annotation tags."""

    line: str
    tags: List[str] = field(default_factory=list)

    @property
    def is_annotated(self) -> bool:
        return bool(self.tags)


@dataclass
class AnnotateResult:
    """Summary of an annotation pass."""

    total: int
    annotated: int
    lines: List[AnnotatedLine]

    @property
    def unannotated(self) -> int:
        return self.total - self.annotated


Rule = Tuple[str, str]  # (pattern, tag)


def _compile_rules(
    rules: Iterable[Rule], case_sensitive: bool
) -> List[Tuple[re.Pattern, str]]:
    flags = 0 if case_sensitive else re.IGNORECASE
    return [(re.compile(pattern, flags), tag) for pattern, tag in rules]


def iter_annotated(
    lines: Iterable[str],
    rules: Iterable[Rule],
    *,
    case_sensitive: bool = False,
    tag_all: bool = True,
) -> Iterator[AnnotatedLine]:
    """Yield AnnotatedLine objects for each input line.

    Args:
        lines:          Iterable of raw log lines.
        rules:          Iterable of (regex_pattern, tag) pairs.
        case_sensitive: Whether pattern matching is case-sensitive.
        tag_all:        If True, collect all matching tags per line.
                        If False, stop after the first matching rule.
    """
    compiled = _compile_rules(rules, case_sensitive)
    for line in lines:
        tags: List[str] = []
        for pattern, tag in compiled:
            if pattern.search(line):
                tags.append(tag)
                if not tag_all:
                    break
        yield AnnotatedLine(line=line, tags=tags)


def annotate(
    lines: Iterable[str],
    rules: Iterable[Rule],
    *,
    case_sensitive: bool = False,
    tag_all: bool = True,
) -> AnnotateResult:
    """Annotate all lines and return a consolidated AnnotateResult."""
    annotated_lines = list(
        iter_annotated(lines, rules, case_sensitive=case_sensitive, tag_all=tag_all)
    )
    annotated_count = sum(1 for al in annotated_lines if al.is_annotated)
    return AnnotateResult(
        total=len(annotated_lines),
        annotated=annotated_count,
        lines=annotated_lines,
    )
