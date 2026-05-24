"""Human-readable and JSON reporters for DiffResult."""
from __future__ import annotations

import json
from typing import Callable

from logslice.differ import DiffResult

_SYMBOLS = {"equal": " ", "insert": "+", "delete": "-"}


def report_diff_text(result: DiffResult) -> str:
    """Return a unified-style text representation of the diff."""
    lines = []
    lines.append(
        f"--- a  ({result.removed} removed, {result.added} added, "
        f"{result.equal} equal, change_ratio={result.change_ratio:.2%})"
    )
    for dl in result.lines:
        sym = _SYMBOLS.get(dl.tag, "?")
        lines.append(f"{sym} {dl.line}")
    return "\n".join(lines)


def report_diff_json(result: DiffResult) -> str:
    """Return a JSON string representation of the diff."""
    payload = {
        "added": result.added,
        "removed": result.removed,
        "equal": result.equal,
        "total": result.total,
        "change_ratio": round(result.change_ratio, 6),
        "lines": [
            {"tag": dl.tag, "source": dl.source, "line": dl.line}
            for dl in result.lines
        ],
    }
    return json.dumps(payload)


def get_diff_reporter(fmt: str = "text") -> Callable[[DiffResult], str]:
    """Return the reporter callable for *fmt* ('text' or 'json')."""
    reporters = {"text": report_diff_text, "json": report_diff_json}
    if fmt not in reporters:
        raise ValueError(f"Unknown diff reporter format: {fmt!r}")
    return reporters[fmt]
