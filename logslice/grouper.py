"""Group log lines into buckets by a time window or a regex key."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional

from .parser import parse_timestamp


@dataclass
class Group:
    key: str
    lines: List[str] = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.lines)


@dataclass
class GroupResult:
    groups: List[Group]
    total_lines: int
    ungrouped: int

    @property
    def group_count(self) -> int:
        return len(self.groups)


def _window_label(ts: datetime, window_seconds: int) -> str:
    epoch = datetime(1970, 1, 1, tzinfo=ts.tzinfo)
    slot = int((ts - epoch).total_seconds() // window_seconds)
    base = epoch + timedelta(seconds=slot * window_seconds)
    return base.strftime("%Y-%m-%dT%H:%M:%S")


def group_by_time(
    lines: Iterable[str],
    window_seconds: int = 60,
) -> GroupResult:
    """Bucket lines by fixed-size time windows."""
    buckets: Dict[str, Group] = {}
    total = 0
    ungrouped = 0

    for line in lines:
        total += 1
        ts = parse_timestamp(line)
        if ts is None:
            ungrouped += 1
            continue
        label = _window_label(ts, window_seconds)
        if label not in buckets:
            buckets[label] = Group(key=label)
        buckets[label].lines.append(line)

    ordered = [buckets[k] for k in sorted(buckets)]
    return GroupResult(groups=ordered, total_lines=total, ungrouped=ungrouped)


def group_by_pattern(
    lines: Iterable[str],
    pattern: str,
    flags: int = re.IGNORECASE,
    fallback_key: str = "__other__",
) -> GroupResult:
    """Bucket lines by the first capturing group of *pattern*."""
    compiled = re.compile(pattern, flags)
    buckets: Dict[str, Group] = {}
    total = 0
    ungrouped = 0

    for line in lines:
        total += 1
        m = compiled.search(line)
        key = m.group(1) if (m and m.lastindex and m.lastindex >= 1) else None
        if key is None:
            ungrouped += 1
            key = fallback_key
        if key not in buckets:
            buckets[key] = Group(key=key)
        buckets[key].lines.append(line)

    return GroupResult(
        groups=list(buckets.values()),
        total_lines=total,
        ungrouped=ungrouped,
    )
