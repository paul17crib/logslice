"""Tests for logslice.encoder."""
from __future__ import annotations

import base64
import binascii

import pytest

from logslice.encoder import EncodeResult, encode, iter_encoded


SAMPLE = ["hello world", "2024-01-01 ERROR something went wrong", "plain line"]


# --- encode() return type ---

def test_encode_returns_encode_result():
    result = encode(SAMPLE)
    assert isinstance(result, EncodeResult)


def test_encode_empty_input():
    result = encode([])
    assert result.total_lines == 0
    assert result.lines == []
    assert result.encoded_ratio == 0.0


def test_encode_total_lines_matches_input():
    result = encode(SAMPLE)
    assert result.total_lines == len(SAMPLE)


def test_encode_base64_correct_values():
    result = encode(["hello"], encoding="base64")
    expected = base64.b64encode(b"hello").decode()
    assert result.lines == [expected]


def test_encode_hex_correct_values():
    result = encode(["hi"], encoding="hex")
    expected = binascii.hexlify(b"hi").decode()
    assert result.lines == [expected]


def test_encode_escape_correct_values():
    result = encode(["tab\there"], encoding="escape")
    expected = "tab\\there"
    assert result.lines[0] == expected


def test_encode_stores_encoding_name():
    result = encode(SAMPLE, encoding="hex")
    assert result.encoding == "hex"


def test_encode_encoded_lines_count_nonzero():
    result = encode(SAMPLE, encoding="base64")
    assert result.encoded_lines == len(SAMPLE)


def test_encode_ratio_is_one_when_all_encoded():
    result = encode(SAMPLE, encoding="base64")
    assert result.encoded_ratio == 1.0


def test_encode_unknown_encoding_raises():
    with pytest.raises(ValueError, match="Unknown encoding"):
        encode(SAMPLE, encoding="rot13")


# --- iter_encoded() ---

def test_iter_encoded_yields_correct_count():
    out = list(iter_encoded(SAMPLE, encoding="hex"))
    assert len(out) == len(SAMPLE)


def test_iter_encoded_base64_reversible():
    for original, encoded in zip(SAMPLE, iter_encoded(SAMPLE, encoding="base64")):
        decoded = base64.b64decode(encoded.encode()).decode()
        assert decoded == original


def test_iter_encoded_hex_reversible():
    for original, encoded in zip(SAMPLE, iter_encoded(SAMPLE, encoding="hex")):
        decoded = binascii.unhexlify(encoded).decode()
        assert decoded == original


def test_iter_encoded_unknown_raises():
    with pytest.raises(ValueError, match="Unknown encoding"):
        list(iter_encoded(SAMPLE, encoding="binary"))


def test_iter_encoded_empty_input_returns_empty():
    assert list(iter_encoded([], encoding="base64")) == []
