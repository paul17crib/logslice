"""Diff two sequences of log lines and report added/removed lines."""
from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Iterable, List


@dataclass
class DiffLine:
    tag: str          # 'equal', 'insert', 'delete', 'replace'
    line: str
    source: str       # 'a', 'b', or 'both'


@dataclass
class DiffResult:
    lines: List[DiffLine] = field(default_factory=list)
    added: int = 0
    removed: int = 0
    equal: int = 0

    @property
    def total(self) -> int:
        return self.added + self.removed + self.equal

    @property
    def change_ratio(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.added + self.removed) / self.total


def diff_logs(
    lines_a: Iterable[str],
    lines_b: Iterable[str],
    context: int = 0,
) -> DiffResult:
    """Compute a line-level diff between two log sequences.

    Parameters
    ----------
    lines_a:  original log lines
    lines_b:  new log lines
    context:  number of equal lines to include around changes (0 = changes only)
    """
    seq_a = list(lines_a)
    seq_b = list(lines_b)

    result = DiffResult()
    matcher = SequenceMatcher(None, seq_a, seq_b, autojunk=False)

    opcodes = matcher.get_opcodes()

    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            lines = seq_a[i1:i2]
            if context > 0:
                lines = lines[:context] if len(lines) > context * 2 else lines
            for ln in lines:
                result.lines.append(DiffLine(tag="equal", line=ln, source="both"))
                result.equal += 1
        elif tag == "insert":
            for ln in seq_b[j1:j2]:
                result.lines.append(DiffLine(tag="insert", line=ln, source="b"))
                result.added += 1
        elif tag == "delete":
            for ln in seq_a[i1:i2]:
                result.lines.append(DiffLine(tag="delete", line=ln, source="a"))
                result.removed += 1
        elif tag == "replace":
            for ln in seq_a[i1:i2]:
                result.lines.append(DiffLine(tag="delete", line=ln, source="a"))
                result.removed += 1
            for ln in seq_b[j1:j2]:
                result.lines.append(DiffLine(tag="insert", line=ln, source="b"))
                result.added += 1

    return result
