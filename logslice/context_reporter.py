"""Reporters for :class:`~logslice.contexter.ContextResult`."""
from __future__ import annotations

import json
from typing import Callable

from logslice.contexter import ContextResult


def report_context_text(result: ContextResult) -> str:
    """Return a human-readable summary followed by the extracted lines."""
    lines = [
        f"Keyword matches : {result.match_count}",
        f"Input lines     : {result.total_input}",
        f"Output lines    : {result.total_output}",
        f"Context window  : ±{result.context_lines // 2 if result.context_lines % 2 == 0 else result.context_lines}",
        "-" * 40,
    ]
    for lineno, text in result.lines:
        lines.append(f"{lineno:>6}: {text.rstrip()}")
    return "\n".join(lines)


def report_context_json(result: ContextResult) -> str:
    """Return a JSON string representation of the context result."""
    payload = {
        "match_count": result.match_count,
        "total_input": result.total_input,
        "total_output": result.total_output,
        "context_lines": result.context_lines,
        "lines": [
            {"lineno": lineno, "text": text.rstrip()}
            for lineno, text in result.lines
        ],
    }
    return json.dumps(payload, indent=2)


def get_context_reporter(fmt: str) -> Callable[[ContextResult], str]:
    """Return the reporter callable for *fmt* (``'text'`` or ``'json'``)."""
    reporters = {
        "text": report_context_text,
        "json": report_context_json,
    }
    if fmt not in reporters:
        raise ValueError(f"Unknown format {fmt!r}. Choose from: {list(reporters)}")
    return reporters[fmt]
