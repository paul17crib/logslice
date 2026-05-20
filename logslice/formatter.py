"""Output formatters for logslice results."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Iterable, Iterator


def format_plain(lines: Iterable[str]) -> Iterator[str]:
    """Yield lines as-is (plain text passthrough)."""
    for line in lines:
        yield line


def format_numbered(lines: Iterable[str], start: int = 1) -> Iterator[str]:
    """Yield lines prefixed with their line number.

    Args:
        lines: Iterable of log lines.
        start: Starting line number (default 1).
    """
    for idx, line in enumerate(lines, start=start):
        yield f"{idx:>6}  {line}"


def format_json_stream(
    lines: Iterable[str],
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> Iterator[str]:
    """Yield each line wrapped in a JSON envelope.

    The first yielded string is a header object, followed by one JSON object
    per log line, then a footer object.

    Args:
        lines: Iterable of log lines.
        start_time: Optional slice start timestamp.
        end_time: Optional slice end timestamp.
    """
    header = {
        "type": "header",
        "start_time": start_time.isoformat() if start_time else None,
        "end_time": end_time.isoformat() if end_time else None,
    }
    yield json.dumps(header)

    count = 0
    for idx, line in enumerate(lines, start=1):
        record = {"type": "line", "n": idx, "text": line.rstrip("\n")}
        yield json.dumps(record)
        count = idx

    footer = {"type": "footer", "total_lines": count}
    yield json.dumps(footer)


FORMATS: dict[str, object] = {
    "plain": format_plain,
    "numbered": format_numbered,
    "json": format_json_stream,
}


def get_formatter(name: str) -> object:
    """Return a formatter callable by name.

    Args:
        name: One of 'plain', 'numbered', 'json'.

    Raises:
        ValueError: If *name* is not a recognised format.
    """
    try:
        return FORMATS[name]
    except KeyError:
        raise ValueError(
            f"Unknown format {name!r}. Choose from: {', '.join(FORMATS)}"
        )
