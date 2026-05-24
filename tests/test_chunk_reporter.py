"""Tests for logslice.chunk_reporter."""
from __future__ import annotations

import json

import pytest

from logslice.chunker import chunk
from logslice.chunk_reporter import get_chunk_reporter, report_chunk_json, report_chunk_text


LINES = ["line one", "line two", "line three", "line four", "line five"]


def _result(size: int = 2):
    return chunk(LINES, chunk_size=size)


def test_report_text_returns_string():
    assert isinstance(report_chunk_text(_result()), str)


def test_report_text_contains_chunk_count():
    text = report_chunk_text(_result(2))
    assert "3" in text  # 3 chunks


def test_report_text_contains_total_lines():
    text = report_chunk_text(_result())
    assert str(len(LINES)) in text


def test_report_text_contains_chunk_index():
    text = report_chunk_text(_result())
    assert "0" in text


def test_report_json_returns_string():
    assert isinstance(report_chunk_json(_result()), str)


def test_report_json_parseable():
    data = json.loads(report_chunk_json(_result()))
    assert isinstance(data, dict)


def test_report_json_has_chunk_count_key():
    data = json.loads(report_chunk_json(_result()))
    assert "chunk_count" in data


def test_report_json_has_total_lines_key():
    data = json.loads(report_chunk_json(_result()))
    assert "total_lines" in data


def test_report_json_chunks_list():
    data = json.loads(report_chunk_json(_result()))
    assert isinstance(data["chunks"], list)


def test_report_json_chunk_has_lines():
    data = json.loads(report_chunk_json(_result()))
    assert "lines" in data["chunks"][0]


def test_get_reporter_text():
    fn = get_chunk_reporter("text")
    assert fn is report_chunk_text


def test_get_reporter_json():
    fn = get_chunk_reporter("json")
    assert fn is report_chunk_json


def test_get_reporter_unknown_raises():
    with pytest.raises(ValueError):
        get_chunk_reporter("xml")
