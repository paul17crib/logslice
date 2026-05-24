"""Human-readable and JSON reporters for ChunkResult."""
from __future__ import annotations

import json
from typing import Callable

from logslice.chunker import ChunkResult


def report_chunk_text(result: ChunkResult) -> str:
    lines = [
        f"Chunks  : {result.chunk_count}",
        f"Total   : {result.total_lines} lines",
    ]
    for chunk in result.chunks:
        lines.append(f"  [{chunk.index:>4}] {chunk.size} lines")
    return "\n".join(lines)


def report_chunk_json(result: ChunkResult) -> str:
    payload = {
        "chunk_count": result.chunk_count,
        "total_lines": result.total_lines,
        "chunks": [
            {"index": c.index, "size": c.size, "lines": c.lines}
            for c in result.chunks
        ],
    }
    return json.dumps(payload, indent=2)


def get_chunk_reporter(fmt: str = "text") -> Callable[[ChunkResult], str]:
    """Return the reporter function for *fmt* ('text' or 'json')."""
    reporters = {"text": report_chunk_text, "json": report_chunk_json}
    if fmt not in reporters:
        raise ValueError(f"Unknown format {fmt!r}; choose from {list(reporters)}")
    return reporters[fmt]
