"""Pipeline: compose multiple logslice transforms into a single pass."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional


@dataclass
class PipelineResult:
    """Holds the final lines and per-stage metadata collected during a run."""

    lines: List[str]
    stage_meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_lines(self) -> int:
        return len(self.lines)


# A stage is any callable that accepts an Iterable[str] and returns an
# Iterable[str].  Stages may also return richer objects (e.g. RedactResult,
# SampleResult) — in that case they must expose a `.lines` attribute.

Stage = Callable[[Iterable[str]], Any]


def _extract_lines(obj: Any) -> List[str]:
    """Pull a plain list of strings out of a stage's return value."""
    if isinstance(obj, list):
        return obj
    if hasattr(obj, "lines"):
        return list(obj.lines)
    # Assume it's a raw iterable
    return list(obj)


def run_pipeline(
    source: Iterable[str],
    stages: List[Stage],
    collect_meta: bool = False,
) -> PipelineResult:
    """Run *source* through each stage in order.

    Parameters
    ----------
    source:
        Initial iterable of log lines.
    stages:
        Ordered list of transform callables.
    collect_meta:
        When *True*, store each stage's raw return value in
        ``PipelineResult.stage_meta`` keyed by stage index.

    Returns
    -------
    PipelineResult
        Final lines after all stages have been applied.
    """
    current: Iterable[str] = source
    meta: Dict[str, Any] = {}

    for idx, stage in enumerate(stages):
        raw = stage(current)
        if collect_meta:
            meta[f"stage_{idx}"] = raw
        current = _extract_lines(raw)

    return PipelineResult(lines=list(current), stage_meta=meta)
