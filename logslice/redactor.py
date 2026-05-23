"""Redactor: mask sensitive patterns in log lines."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional, Tuple

# Built-in pattern presets
PRESET_PATTERNS: dict[str, str] = {
    "ipv4": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "email": r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    "token": r"(?i)(?:token|api[_-]?key|secret)[=:\s]+\S+",
    "credit_card": r"\b(?:\d[ -]?){13,16}\b",
    "uuid": r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
}

REDACT_PLACEHOLDER = "[REDACTED]"


@dataclass
class RedactResult:
    lines: List[str]
    total_lines: int
    redacted_lines: int
    redaction_count: int

    @property
    def redaction_ratio(self) -> float:
        if self.total_lines == 0:
            return 0.0
        return self.redacted_lines / self.total_lines


def _compile_rules(
    patterns: List[str],
    presets: Optional[List[str]] = None,
) -> List[re.Pattern]:
    compiled: List[re.Pattern] = []
    for preset in (presets or []):
        raw = PRESET_PATTERNS.get(preset)
        if raw is None:
            raise ValueError(f"Unknown preset: {preset!r}")
        compiled.append(re.compile(raw))
    for pat in patterns:
        compiled.append(re.compile(pat))
    return compiled


def iter_redacted(
    lines: Iterable[str],
    patterns: Optional[List[str]] = None,
    presets: Optional[List[str]] = None,
    placeholder: str = REDACT_PLACEHOLDER,
) -> Iterator[Tuple[str, int]]:
    """Yield (redacted_line, substitution_count) for each input line."""
    rules = _compile_rules(patterns or [], presets)
    for line in lines:
        count = 0
        result = line
        for rule in rules:
            result, n = rule.subn(placeholder, result)
            count += n
        yield result, count


def redact(
    lines: Iterable[str],
    patterns: Optional[List[str]] = None,
    presets: Optional[List[str]] = None,
    placeholder: str = REDACT_PLACEHOLDER,
) -> RedactResult:
    """Redact sensitive patterns from *lines* and return a RedactResult."""
    out_lines: List[str] = []
    total = 0
    redacted_lines = 0
    redaction_count = 0

    for redacted, count in iter_redacted(lines, patterns=patterns, presets=presets, placeholder=placeholder):
        out_lines.append(redacted)
        total += 1
        if count:
            redacted_lines += 1
            redaction_count += count

    return RedactResult(
        lines=out_lines,
        total_lines=total,
        redacted_lines=redacted_lines,
        redaction_count=redaction_count,
    )
