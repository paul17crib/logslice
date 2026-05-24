"""Reporters for ScoreResult — text and JSON output."""
from __future__ import annotations

import json
from typing import Callable

from logslice.scorer import ScoreResult


def report_score_text(result: ScoreResult) -> str:
    """Render a ScoreResult as a human-readable text report."""
    lines = [
        "=== Score Report ===",
        f"Total lines examined : {result.total_lines}",
        f"Lines kept           : {result.scored_lines}",
        f"Max score            : {result.max_score:.4f}",
        f"Min score            : {result.min_score:.4f}",
        f"Mean score           : {result.mean_score:.4f}",
        "",
        "--- Scored Lines ---",
    ]
    for sl in result.lines:
        terms = ", ".join(sl.matched_terms) if sl.matched_terms else "(none)"
        lines.append(f"[{sl.score:+.2f}] ({terms}) {sl.line.rstrip()}")  
    return "\n".join(lines)


def report_score_json(result: ScoreResult) -> str:
    """Render a ScoreResult as a JSON string."""
    payload = {
        "total_lines": result.total_lines,
        "scored_lines": result.scored_lines,
        "max_score": result.max_score,
        "min_score": result.min_score,
        "mean_score": result.mean_score,
        "lines": [
            {
                "line": sl.line.rstrip(),
                "score": sl.score,
                "matched_terms": sl.matched_terms,
            }
            for sl in result.lines
        ],
    }
    return json.dumps(payload, indent=2)


def get_score_reporter(fmt: str = "text") -> Callable[[ScoreResult], str]:
    """Return the reporter callable for the given format name."""
    reporters = {
        "text": report_score_text,
        "json": report_score_json,
    }
    if fmt not in reporters:
        raise ValueError(f"Unknown format {fmt!r}. Choose from: {list(reporters)}")
    return reporters[fmt]
