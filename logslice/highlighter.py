"""Keyword highlighting for log output.

Provides utilities to annotate log lines that contain one or more
keywords, either with ANSI colour codes (terminal) or with plain
markers suitable for non-colour environments.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional

ANSI_YELLOW = "\033[33m"
ANSI_RED = "\033[31m"
ANSI_RESET = "\033[0m"

_LEVEL_COLOURS = {
    "warn": ANSI_YELLOW,
    "warning": ANSI_YELLOW,
    "error": ANSI_RED,
    "err": ANSI_RED,
    "critical": ANSI_RED,
    "fatal": ANSI_RED,
}


@dataclass
class HighlightResult:
    """Outcome of a highlight pass over a sequence of lines."""

    lines: List[str] = field(default_factory=list)
    matched_count: int = 0


def _build_pattern(keywords: Iterable[str], case_sensitive: bool) -> re.Pattern:
    flags = 0 if case_sensitive else re.IGNORECASE
    parts = [re.escape(kw) for kw in keywords if kw]
    if not parts:
        raise ValueError("At least one non-empty keyword is required.")
    return re.compile("|".join(parts), flags)


def highlight_ansi(
    lines: Iterable[str],
    keywords: Iterable[str],
    *,
    case_sensitive: bool = False,
) -> HighlightResult:
    """Wrap matching keywords in ANSI colour codes.

    Lines that contain a severity keyword (error, warn, …) are coloured
    by severity; otherwise yellow is used for generic keyword matches.
    """
    pattern = _build_pattern(keywords, case_sensitive)
    result = HighlightResult()
    for line in lines:
        if pattern.search(line):
            result.matched_count += 1
            lower = line.lower()
            colour = ANSI_YELLOW
            for token, col in _LEVEL_COLOURS.items():
                if token in lower:
                    colour = col
                    break
            highlighted = pattern.sub(
                lambda m: f"{colour}{m.group()}{ANSI_RESET}", line
            )
            result.lines.append(highlighted)
        else:
            result.lines.append(line)
    return result


def highlight_plain(
    lines: Iterable[str],
    keywords: Iterable[str],
    *,
    marker: str = ">>>",
    case_sensitive: bool = False,
) -> HighlightResult:
    """Prefix matching lines with a plain-text marker."""
    pattern = _build_pattern(keywords, case_sensitive)
    result = HighlightResult()
    for line in lines:
        if pattern.search(line):
            result.matched_count += 1
            result.lines.append(f"{marker} {line}")
        else:
            result.lines.append(line)
    return result


def get_highlighter(mode: str = "ansi"):
    """Return the highlight function for *mode* ('ansi' or 'plain')."""
    if mode == "plain":
        return highlight_plain
    if mode == "ansi":
        return highlight_ansi
    raise ValueError(f"Unknown highlight mode: {mode!r}. Choose 'ansi' or 'plain'.")
