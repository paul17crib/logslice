"""Log line classifier: assigns severity levels to log lines based on patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional

# Default severity patterns ordered from highest to lowest priority
_DEFAULT_RULES: List[tuple[str, str]] = [
    ("CRITICAL", r"\b(critical|fatal|emergency)\b"),
    ("ERROR",    r"\b(error|err|exception|traceback)\b"),
    ("WARNING",  r"\b(warn(?:ing)?|deprecated)\b"),
    ("INFO",     r"\b(info|notice|started|stopped|ready)\b"),
    ("DEBUG",    r"\b(debug|verbose|trace)\b"),
]

SEVERITY_ORDER = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


@dataclass
class ClassifiedLine:
    line: str
    severity: Optional[str]  # None means unclassified

    @property
    def is_classified(self) -> bool:
        return self.severity is not None


@dataclass
class ClassifyResult:
    lines: List[ClassifiedLine] = field(default_factory=list)
    total: int = 0
    classified: int = 0

    @property
    def unclassified(self) -> int:
        return self.total - self.classified

    def counts_by_severity(self) -> dict[str, int]:
        counts: dict[str, int] = {s: 0 for s in SEVERITY_ORDER}
        for cl in self.lines:
            if cl.severity and cl.severity in counts:
                counts[cl.severity] += 1
        return counts


def _compile_rules(
    rules: Optional[List[tuple[str, str]]] = None,
    case_sensitive: bool = False,
) -> List[tuple[str, re.Pattern]]:
    if rules is None:
        rules = _DEFAULT_RULES
    flags = 0 if case_sensitive else re.IGNORECASE
    return [(label, re.compile(pattern, flags)) for label, pattern in rules]


def iter_classified(
    lines: Iterable[str],
    rules: Optional[List[tuple[str, str]]] = None,
    case_sensitive: bool = False,
) -> Iterator[ClassifiedLine]:
    compiled = _compile_rules(rules, case_sensitive)
    for line in lines:
        severity = None
        for label, pattern in reversed(compiled):  # highest priority wins
            if pattern.search(line):
                severity = label
        yield ClassifiedLine(line=line, severity=severity)


def classify(
    lines: Iterable[str],
    rules: Optional[List[tuple[str, str]]] = None,
    case_sensitive: bool = False,
) -> ClassifyResult:
    result = ClassifyResult()
    for cl in iter_classified(lines, rules=rules, case_sensitive=case_sensitive):
        result.lines.append(cl)
        result.total += 1
        if cl.is_classified:
            result.classified += 1
    return result
