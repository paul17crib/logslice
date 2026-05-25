"""Line transformer: apply a sequence of string transformations to log lines."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Iterable, List, Optional


_Transform = Callable[[str], str]


@dataclass
class TransformResult:
    lines: List[str]
    total_lines: int
    changed_lines: int
    transforms_applied: List[str]

    @property
    def change_ratio(self) -> float:
        if self.total_lines == 0:
            return 0.0
        return self.changed_lines / self.total_lines


def _make_upper(line: str) -> str:
    return line.upper()


def _make_lower(line: str) -> str:
    return line.lower()


def _strip_ansi(line: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", line)


def _prefix_factory(prefix: str) -> _Transform:
    def _apply(line: str) -> str:
        return prefix + line
    _apply.__name__ = f"prefix:{prefix!r}"
    return _apply


def _suffix_factory(suffix: str) -> _Transform:
    def _apply(line: str) -> str:
        return line + suffix
    _apply.__name__ = f"suffix:{suffix!r}"
    return _apply


_BUILTIN: dict[str, _Transform] = {
    "upper": _make_upper,
    "lower": _make_lower,
    "strip_ansi": _strip_ansi,
}


def _resolve_transforms(
    names: List[str],
    extra: Optional[List[_Transform]] = None,
) -> List[_Transform]:
    resolved: List[_Transform] = []
    for name in names:
        if name in _BUILTIN:
            resolved.append(_BUILTIN[name])
        elif name.startswith("prefix:"):
            resolved.append(_prefix_factory(name[7:]))
        elif name.startswith("suffix:"):
            resolved.append(_suffix_factory(name[7:]))
        else:
            raise ValueError(f"Unknown transform: {name!r}")
    if extra:
        resolved.extend(extra)
    return resolved


def transform(
    lines: Iterable[str],
    transforms: List[str],
    extra: Optional[List[_Transform]] = None,
) -> TransformResult:
    """Apply named (and optional callable) transforms to each line."""
    fns = _resolve_transforms(transforms, extra)
    fn_names = [getattr(f, "__name__", repr(f)) for f in fns]
    result_lines: List[str] = []
    total = 0
    changed = 0
    for line in lines:
        total += 1
        out = line
        for fn in fns:
            out = fn(out)
        if out != line:
            changed += 1
        result_lines.append(out)
    return TransformResult(
        lines=result_lines,
        total_lines=total,
        changed_lines=changed,
        transforms_applied=fn_names,
    )
