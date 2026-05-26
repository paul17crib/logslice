"""Line normalizer: strips, collapses whitespace, and optionally lowercases log lines."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List


@dataclass
class NormalizeResult:
    lines: List[str]
    total: int
    changed: int

    @property
    def unchanged(self) -> int:
        return self.total - self.changed

    @property
    def change_ratio(self) -> float:
        return self.changed / self.total if self.total else 0.0


_MULTI_SPACE = re.compile(r" {2,}")
_TRAILING_NEWLINE = re.compile(r"[\r\n]+$")


def _normalize_line(
    line: str,
    *,
    strip: bool = True,
    collapse_whitespace: bool = True,
    lowercase: bool = False,
) -> str:
    """Apply normalization transforms to a single line."""
    result = _TRAILING_NEWLINE.sub("", line)
    if strip:
        result = result.strip()
    if collapse_whitespace:
        result = _MULTI_SPACE.sub(" ", result)
    if lowercase:
        result = result.lower()
    return result


def iter_normalized(
    lines: Iterable[str],
    *,
    strip: bool = True,
    collapse_whitespace: bool = True,
    lowercase: bool = False,
) -> Iterator[str]:
    """Yield normalized lines one at a time."""
    for line in lines:
        yield _normalize_line(
            line,
            strip=strip,
            collapse_whitespace=collapse_whitespace,
            lowercase=lowercase,
        )


def normalize(
    lines: Iterable[str],
    *,
    strip: bool = True,
    collapse_whitespace: bool = True,
    lowercase: bool = False,
) -> NormalizeResult:
    """Normalize all lines and return a NormalizeResult."""
    total = 0
    changed = 0
    out: List[str] = []
    for line in lines:
        # Strip trailing newlines before comparing so that the presence of a
        # newline character alone does not count as a change.
        original = _TRAILING_NEWLINE.sub("", line)
        normalized = _normalize_line(
            line,
            strip=strip,
            collapse_whitespace=collapse_whitespace,
            lowercase=lowercase,
        )
        out.append(normalized)
        total += 1
        if normalized != original:
            changed += 1
    return NormalizeResult(lines=out, total=total, changed=changed)


def normalize_line(
    line: str,
    *,
    strip: bool = True,
    collapse_whitespace: bool = True,
    lowercase: bool = False,
) -> str:
    """Public wrapper around the internal line normalization logic.

    Useful when callers need to normalize a single line without building a
    full :class:`NormalizeResult`.

    Args:
        line: The raw log line to normalize.
        strip: Whether to strip leading/trailing whitespace.
        collapse_whitespace: Whether to collapse runs of spaces to a single space.
        lowercase: Whether to convert the line to lowercase.

    Returns:
        The normalized line string.
    """
    return _normalize_line(
        line,
        strip=strip,
        collapse_whitespace=collapse_whitespace,
        lowercase=lowercase,
    )
