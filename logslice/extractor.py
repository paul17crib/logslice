"""Field extractor – pull structured key=value (or JSON) fields from log lines."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional

_KV_RE = re.compile(r'([\w.\-]+)=(?:"([^"]*)"|([^\s,]*))')


@dataclass
class ExtractedLine:
    raw: str
    fields: Dict[str, str]

    @property
    def is_structured(self) -> bool:
        return bool(self.fields)


@dataclass
class ExtractResult:
    lines: List[ExtractedLine]
    total_lines: int
    structured_lines: int
    all_keys: List[str]

    @property
    def unstructured_lines(self) -> int:
        return self.total_lines - self.structured_lines


def _extract_kv(line: str) -> Dict[str, str]:
    return {m.group(1): (m.group(2) if m.group(2) is not None else m.group(3))
            for m in _KV_RE.finditer(line)}


def _extract_json(line: str) -> Optional[Dict[str, str]]:
    stripped = line.strip()
    if not stripped.startswith("{"):
        return None
    try:
        obj = json.loads(stripped)
        if isinstance(obj, dict):
            return {str(k): str(v) for k, v in obj.items()}
    except json.JSONDecodeError:
        pass
    return None


def iter_extracted(
    lines: Iterable[str],
    *,
    prefer_json: bool = True,
    keys: Optional[List[str]] = None,
) -> Iterator[ExtractedLine]:
    """Yield ExtractedLine for each input line."""
    for raw in lines:
        fields: Dict[str, str] = {}
        if prefer_json:
            fields = _extract_json(raw) or _extract_kv(raw)
        else:
            fields = _extract_kv(raw) or (_extract_json(raw) or {})
        if keys:
            fields = {k: v for k, v in fields.items() if k in keys}
        yield ExtractedLine(raw=raw, fields=fields)


def extract(
    lines: Iterable[str],
    *,
    prefer_json: bool = True,
    keys: Optional[List[str]] = None,
) -> ExtractResult:
    """Extract fields from all lines and return an ExtractResult."""
    extracted: List[ExtractedLine] = list(
        iter_extracted(lines, prefer_json=prefer_json, keys=keys)
    )
    structured = sum(1 for e in extracted if e.is_structured)
    seen_keys: Dict[str, None] = {}
    for e in extracted:
        for k in e.fields:
            seen_keys[k] = None
    return ExtractResult(
        lines=extracted,
        total_lines=len(extracted),
        structured_lines=structured,
        all_keys=list(seen_keys),
    )
