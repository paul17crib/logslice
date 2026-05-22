"""Truncator: truncate long log lines to a maximum character width."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator

_DEFAULT_MAX_WIDTH = 200
_DEFAULT_SUFFIX = "..."


@dataclass
class TruncateResult:
    """Result of a truncation pass over a sequence of lines."""

    lines: list[str] = field(default_factory=list)
    total_lines: int = 0
    truncated_lines: int = 0

    @property
    def truncation_ratio(self) -> float:
        """Fraction of lines that were truncated (0.0 – 1.0)."""
        if self.total_lines == 0:
            return 0.0
        return self.truncated_lines / self.total_lines


def _truncate_line(line: str, max_width: int, suffix: str) -> tuple[str, bool]:
    """Return *(possibly truncated line, was_truncated)*."""
    # Strip trailing newline for measurement, reattach afterwards.
    stripped = line.rstrip("\n")
    if len(stripped) <= max_width:
        return line, False
    truncated = stripped[:max_width] + suffix
    # Preserve a trailing newline if the original had one.
    if line.endswith("\n"):
        truncated += "\n"
    return truncated, True


def iter_truncated(
    lines: Iterable[str],
    max_width: int = _DEFAULT_MAX_WIDTH,
    suffix: str = _DEFAULT_SUFFIX,
) -> Iterator[str]:
    """Yield lines, truncating any that exceed *max_width* visible characters."""
    if max_width < 1:
        raise ValueError(f"max_width must be >= 1, got {max_width}")
    for line in lines:
        result, _ = _truncate_line(line, max_width, suffix)
        yield result


def truncate(
    lines: Iterable[str],
    max_width: int = _DEFAULT_MAX_WIDTH,
    suffix: str = _DEFAULT_SUFFIX,
) -> TruncateResult:
    """Truncate *lines* and return a :class:`TruncateResult` with statistics."""
    if max_width < 1:
        raise ValueError(f"max_width must be >= 1, got {max_width}")
    result = TruncateResult()
    for line in lines:
        out, was_truncated = _truncate_line(line, max_width, suffix)
        result.lines.append(out)
        result.total_lines += 1
        if was_truncated:
            result.truncated_lines += 1
    return result
