"""Reporter for ExtractResult – text and JSON output."""
from __future__ import annotations

import json
from typing import Callable

from logslice.extractor import ExtractResult


def report_extract_text(result: ExtractResult) -> str:
    lines = [
        f"Total lines    : {result.total_lines}",
        f"Structured     : {result.structured_lines}",
        f"Unstructured   : {result.unstructured_lines}",
        f"Unique keys    : {len(result.all_keys)}",
    ]
    if result.all_keys:
        lines.append("Keys           : " + ", ".join(sorted(result.all_keys)))
    lines.append("")
    for el in result.lines:
        if el.is_structured:
            pairs = "  ".join(f"{k}={v}" for k, v in el.fields.items())
            lines.append(f"  [{pairs}]  {el.raw.rstrip()}")
        else:
            lines.append(f"  (unstructured)  {el.raw.rstrip()}")
    return "\n".join(lines)


def report_extract_json(result: ExtractResult) -> str:
    payload = {
        "total_lines": result.total_lines,
        "structured_lines": result.structured_lines,
        "unstructured_lines": result.unstructured_lines,
        "all_keys": sorted(result.all_keys),
        "lines": [
            {"raw": el.raw.rstrip(), "fields": el.fields}
            for el in result.lines
        ],
    }
    return json.dumps(payload, indent=2)


def get_extract_reporter(fmt: str = "text") -> Callable[[ExtractResult], str]:
    """Return the reporter callable for the requested format."""
    if fmt == "json":
        return report_extract_json
    return report_extract_text
