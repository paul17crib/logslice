"""Log line compressor: collapses consecutive repeated lines into a single
line with a repetition count, similar to syslog's 'last message repeated N
times' behaviour."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, List


@dataclass
class CompressResult:
    """Result returned by :func:`compress`."""

    lines: List[str]
    original_count: int
    compressed_count: int
    collapsed_runs: int

    @property
    def ratio(self) -> float:
        """Fraction of lines removed (0.0 – 1.0)."""
        if self.original_count == 0:
            return 0.0
        return 1.0 - self.compressed_count / self.original_count


def _repeat_label(line: str, count: int, template: str) -> str:
    return template.format(line=line, count=count)


def iter_compressed(
    lines: Iterable[str],
    *,
    template: str = "{line} [x{count}]",
    min_run: int = 2,
) -> Iterator[str]:
    """Yield lines with consecutive duplicates collapsed.

    Parameters
    ----------
    lines:
        Input lines (strings, newline-stripped or not).
    template:
        Format string used when a run is collapsed.  Receives ``{line}`` and
        ``{count}`` placeholders.
    min_run:
        Minimum consecutive repetitions before collapsing (default 2).
    """
    prev: str | None = None
    run: int = 0

    for raw in lines:
        line = raw.rstrip("\n")
        if line == prev:
            run += 1
        else:
            if prev is not None:
                if run >= min_run:
                    yield _repeat_label(prev, run, template)
                else:
                    for _ in range(run):
                        yield prev
            prev = line
            run = 1

    if prev is not None:
        if run >= min_run:
            yield _repeat_label(prev, run, template)
        else:
            for _ in range(run):
                yield prev


def compress(
    lines: Iterable[str],
    *,
    template: str = "{line} [x{count}]",
    min_run: int = 2,
) -> CompressResult:
    """Compress *lines* and return a :class:`CompressResult`."""
    source = list(lines)
    original_count = len(source)

    out: List[str] = []
    collapsed_runs = 0
    prev: str | None = None
    run = 0

    for raw in source:
        line = raw.rstrip("\n")
        if line == prev:
            run += 1
        else:
            if prev is not None:
                if run >= min_run:
                    out.append(_repeat_label(prev, run, template))
                    collapsed_runs += 1
                else:
                    out.extend([prev] * run)
            prev = line
            run = 1

    if prev is not None:
        if run >= min_run:
            out.append(_repeat_label(prev, run, template))
            collapsed_runs += 1
        else:
            out.extend([prev] * run)

    return CompressResult(
        lines=out,
        original_count=original_count,
        compressed_count=len(out),
        collapsed_runs=collapsed_runs,
    )
