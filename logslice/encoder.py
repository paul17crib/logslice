"""Encode log lines into various output formats (base64, hex, escaped)."""
from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List


_ENCODINGS = ("base64", "hex", "escape")


@dataclass
class EncodeResult:
    lines: List[str]
    encoding: str
    total_lines: int
    encoded_lines: int

    @property
    def encoded_ratio(self) -> float:
        if self.total_lines == 0:
            return 0.0
        return self.encoded_lines / self.total_lines


def _encode_line(line: str, encoding: str) -> str:
    """Encode a single line according to *encoding*."""
    if encoding == "base64":
        return base64.b64encode(line.encode()).decode()
    if encoding == "hex":
        return binascii.hexlify(line.encode()).decode()
    if encoding == "escape":
        return line.encode("unicode_escape").decode()
    raise ValueError(f"Unknown encoding: {encoding!r}. Choose from {_ENCODINGS}.")


def iter_encoded(
    lines: Iterable[str],
    encoding: str = "base64",
) -> Iterator[str]:
    """Yield each line encoded with *encoding*."""
    if encoding not in _ENCODINGS:
        raise ValueError(f"Unknown encoding: {encoding!r}. Choose from {_ENCODINGS}.")
    for line in lines:
        yield _encode_line(line, encoding)


def encode(
    lines: Iterable[str],
    encoding: str = "base64",
) -> EncodeResult:
    """Encode *lines* and return an :class:`EncodeResult`.

    Parameters
    ----------
    lines:
        Iterable of raw log lines.
    encoding:
        One of ``"base64"``, ``"hex"``, or ``"escape"``.
    """
    if encoding not in _ENCODINGS:
        raise ValueError(f"Unknown encoding: {encoding!r}. Choose from {_ENCODINGS}.")

    collected: List[str] = []
    encoded_count = 0
    for line in lines:
        encoded = _encode_line(line, encoding)
        collected.append(encoded)
        if encoded != line:
            encoded_count += 1

    return EncodeResult(
        lines=collected,
        encoding=encoding,
        total_lines=len(collected),
        encoded_lines=encoded_count,
    )
