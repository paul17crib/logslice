"""Score log lines by relevance using keyword weights."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass
class ScoredLine:
    line: str
    score: float
    matched_terms: List[str] = field(default_factory=list)


@dataclass
class ScoreResult:
    lines: List[ScoredLine]
    total_lines: int
    scored_lines: int
    max_score: float
    min_score: float

    @property
    def mean_score(self) -> float:
        if not self.lines:
            return 0.0
        return sum(sl.score for sl in self.lines) / len(self.lines)


def _compile_weights(
    weights: Dict[str, float]
) -> List[Tuple[re.Pattern, float, str]]:
    compiled = []
    for term, weight in weights.items():
        compiled.append((re.compile(re.escape(term), re.IGNORECASE), weight, term))
    return compiled


def score_lines(
    lines: Iterable[str],
    weights: Dict[str, float],
    threshold: Optional[float] = None,
) -> ScoreResult:
    """Score each line by summing weights of matched keywords.

    Args:
        lines: Iterable of log line strings.
        weights: Mapping of keyword -> numeric weight (can be negative).
        threshold: If given, only lines with score >= threshold are included.

    Returns:
        ScoreResult with scored lines and aggregate statistics.
    """
    compiled = _compile_weights(weights)
    all_lines: List[ScoredLine] = []
    total = 0

    for line in lines:
        total += 1
        score = 0.0
        matched: List[str] = []
        for pattern, weight, term in compiled:
            if pattern.search(line):
                score += weight
                matched.append(term)
        all_lines.append(ScoredLine(line=line, score=score, matched_terms=matched))

    if threshold is not None:
        kept = [sl for sl in all_lines if sl.score >= threshold]
    else:
        kept = all_lines

    scores = [sl.score for sl in kept] if kept else [0.0]
    return ScoreResult(
        lines=kept,
        total_lines=total,
        scored_lines=len(kept),
        max_score=max(scores),
        min_score=min(scores),
    )
