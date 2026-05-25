"""Tokenizer: splits log lines into structured tokens (words, numbers, punctuation)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List

_TOKEN_RE = re.compile(
    r"(?P<timestamp>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)"
    r"|(?P<number>-?\d+(?:\.\d+)?)"
    r"|(?P<word>[A-Za-z_][A-Za-z0-9_./-]*)"
    r"|(?P<punct>[^\w\s])"
    r"|(?P<whitespace>\s+)"
)


@dataclass
class Token:
    kind: str   # 'timestamp' | 'number' | 'word' | 'punct' | 'whitespace'
    value: str

    def __repr__(self) -> str:  # pragma: no cover
        return f"Token({self.kind!r}, {self.value!r})"


@dataclass
class TokenizedLine:
    raw: str
    tokens: List[Token] = field(default_factory=list)

    @property
    def word_count(self) -> int:
        return sum(1 for t in self.tokens if t.kind == "word")

    @property
    def number_count(self) -> int:
        return sum(1 for t in self.tokens if t.kind == "number")

    @property
    def has_timestamp(self) -> bool:
        return any(t.kind == "timestamp" for t in self.tokens)


@dataclass
class TokenizeResult:
    lines: List[TokenizedLine]

    @property
    def total_lines(self) -> int:
        return len(self.lines)

    @property
    def total_tokens(self) -> int:
        return sum(len(l.tokens) for l in self.lines)

    @property
    def lines_with_timestamps(self) -> int:
        return sum(1 for l in self.lines if l.has_timestamp)


def _tokenize_line(raw: str) -> TokenizedLine:
    tokens = [
        Token(kind=m.lastgroup, value=m.group())
        for m in _TOKEN_RE.finditer(raw)
    ]
    return TokenizedLine(raw=raw, tokens=tokens)


def iter_tokenized(lines: Iterable[str]) -> Iterator[TokenizedLine]:
    """Yield a TokenizedLine for each input line."""
    for line in lines:
        yield _tokenize_line(line)


def tokenize(lines: Iterable[str]) -> TokenizeResult:
    """Tokenize all lines and return a TokenizeResult."""
    return TokenizeResult(lines=list(iter_tokenized(lines)))
