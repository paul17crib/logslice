"""Tests for logslice.tokenizer."""

from __future__ import annotations

import pytest

from logslice.tokenizer import (
    Token,
    TokenizedLine,
    TokenizeResult,
    iter_tokenized,
    tokenize,
)


SAMPLE_LINES = [
    "2024-01-15T12:00:00Z INFO  server started on port 8080",
    "2024-01-15T12:00:01Z ERROR failed to bind: address already in use",
    "continuation line with no timestamp",
    "latency=123.45ms requests=99",
]


def test_tokenize_returns_tokenize_result():
    result = tokenize(SAMPLE_LINES)
    assert isinstance(result, TokenizeResult)


def test_tokenize_total_lines():
    result = tokenize(SAMPLE_LINES)
    assert result.total_lines == len(SAMPLE_LINES)


def test_tokenize_total_tokens_positive():
    result = tokenize(SAMPLE_LINES)
    assert result.total_tokens > 0


def test_tokenize_lines_with_timestamps():
    result = tokenize(SAMPLE_LINES)
    # first two lines have ISO timestamps
    assert result.lines_with_timestamps == 2


def test_tokenize_empty_input():
    result = tokenize([])
    assert result.total_lines == 0
    assert result.total_tokens == 0
    assert result.lines_with_timestamps == 0


def test_tokenized_line_has_timestamp_true():
    line = next(iter_tokenized(["2024-01-15T12:00:00Z INFO msg"]))
    assert line.has_timestamp is True


def test_tokenized_line_has_timestamp_false():
    line = next(iter_tokenized(["plain log line without date"]))
    assert line.has_timestamp is False


def test_tokenized_line_word_count():
    line = next(iter_tokenized(["hello world foo"]))
    assert line.word_count == 3


def test_tokenized_line_number_count():
    line = next(iter_tokenized(["port 8080 latency 23.5"]))
    assert line.number_count == 2


def test_token_kinds_are_valid():
    valid_kinds = {"timestamp", "number", "word", "punct", "whitespace"}
    result = tokenize(SAMPLE_LINES)
    for tl in result.lines:
        for tok in tl.tokens:
            assert tok.kind in valid_kinds


def test_token_values_reconstruct_raw():
    raw = "2024-01-15T12:00:00Z ERROR code=404"
    tl = next(iter_tokenized([raw]))
    reconstructed = "".join(t.value for t in tl.tokens)
    assert reconstructed == raw


def test_iter_tokenized_yields_tokenized_line():
    for tl in iter_tokenized(SAMPLE_LINES):
        assert isinstance(tl, TokenizedLine)


def test_tokenized_line_raw_preserved():
    raw = "some raw log line"
    tl = next(iter_tokenized([raw]))
    assert tl.raw == raw
