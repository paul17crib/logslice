"""Pipeline: chain slice → deduplicate → highlight → format in one call."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from logslice.deduplicator import deduplicate, DedupeResult
from logslice.formatter import get_formatter
from logslice.highlighter import get_highlighter, HighlightResult
from logslice.slicer import slice_log


@dataclass
class PipelineResult:
    """Aggregated result from a full pipeline run."""

    formatted_lines: list[str]
    dedupe: DedupeResult | None
    highlight: HighlightResult | None
    total_output_lines: int


def run_pipeline(
    log_path: str,
    *,
    start: datetime | None = None,
    end: datetime | None = None,
    # deduplication
    dedupe: bool = False,
    dedupe_consecutive: bool = False,
    # highlighting
    pattern: str | None = None,
    highlight_mode: str = "plain",
    case_sensitive: bool = False,
    # formatting
    fmt: str = "plain",
    numbered: bool = False,
) -> PipelineResult:
    """Run the full logslice pipeline on *log_path*.

    Steps
    -----
    1. Slice the log file to the requested time range.
    2. Optionally deduplicate lines.
    3. Optionally highlight lines matching *pattern*.
    4. Format the output with the chosen formatter.
    """
    # 1. Slice
    raw_lines: list[str] = list(slice_log(log_path, start=start, end=end))

    # 2. Deduplicate
    dedupe_result: DedupeResult | None = None
    if dedupe or dedupe_consecutive:
        dedupe_result = deduplicate(
            raw_lines,
            consecutive_only=dedupe_consecutive,
        )
        working_lines: list[str] = dedupe_result.lines
    else:
        working_lines = raw_lines

    # 3. Highlight
    highlight_result: HighlightResult | None = None
    if pattern:
        highlighter = get_highlighter(highlight_mode)
        highlight_result = highlighter(
            working_lines,
            pattern=pattern,
            case_sensitive=case_sensitive,
        )
        working_lines = highlight_result.lines

    # 4. Format
    formatter_name = "numbered" if numbered else fmt
    formatter = get_formatter(formatter_name)
    formatted: list[str] = list(formatter(working_lines))

    return PipelineResult(
        formatted_lines=formatted,
        dedupe=dedupe_result,
        highlight=highlight_result,
        total_output_lines=len(formatted),
    )
