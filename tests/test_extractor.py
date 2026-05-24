"""Tests for logslice.extractor and logslice.extract_reporter."""
import json
import pytest

from logslice.extractor import (
    ExtractedLine,
    ExtractResult,
    extract,
    iter_extracted,
)
from logslice.extract_reporter import (
    get_extract_reporter,
    report_extract_json,
    report_extract_text,
)

_KV_LINES = [
    "2024-01-01 level=INFO msg=\"server started\" port=8080",
    "2024-01-01 level=ERROR msg=\"disk full\" path=/var/log",
    "continuation line with no fields",
]

_JSON_LINES = [
    '{"level": "WARN", "msg": "high memory", "used": "90%"}',
    '{"level": "DEBUG", "msg": "tick"}',
    "plain text line",
]


def test_extract_returns_extract_result():
    result = extract(_KV_LINES)
    assert isinstance(result, ExtractResult)


def test_extract_total_lines():
    result = extract(_KV_LINES)
    assert result.total_lines == 3


def test_extract_structured_lines_count():
    result = extract(_KV_LINES)
    assert result.structured_lines == 2


def test_extract_unstructured_lines_count():
    result = extract(_KV_LINES)
    assert result.unstructured_lines == 1


def test_extract_all_keys_populated():
    result = extract(_KV_LINES)
    assert "level" in result.all_keys
    assert "msg" in result.all_keys
    assert "port" in result.all_keys


def test_extract_lines_are_extracted_line_instances():
    result = extract(_KV_LINES)
    for el in result.lines:
        assert isinstance(el, ExtractedLine)


def test_extract_kv_fields_correct():
    result = extract(["level=ERROR code=42"])
    el = result.lines[0]
    assert el.fields["level"] == "ERROR"
    assert el.fields["code"] == "42"


def test_extract_json_prefer_json():
    result = extract(_JSON_LINES, prefer_json=True)
    assert result.structured_lines == 2
    assert result.lines[0].fields["level"] == "WARN"


def test_extract_keys_filter():
    result = extract(_KV_LINES, keys=["level"])
    for el in result.lines:
        for k in el.fields:
            assert k == "level"


def test_extract_empty_input():
    result = extract([])
    assert result.total_lines == 0
    assert result.structured_lines == 0
    assert result.all_keys == []


def test_iter_extracted_yields_extracted_line():
    for el in iter_extracted(_KV_LINES):
        assert isinstance(el, ExtractedLine)


def test_report_text_returns_string():
    result = extract(_KV_LINES)
    out = report_extract_text(result)
    assert isinstance(out, str)


def test_report_text_contains_counts():
    result = extract(_KV_LINES)
    out = report_extract_text(result)
    assert "3" in out
    assert "2" in out


def test_report_text_contains_keys():
    result = extract(_KV_LINES)
    out = report_extract_text(result)
    assert "level" in out


def test_report_json_is_valid_json():
    result = extract(_JSON_LINES)
    out = report_extract_json(result)
    payload = json.loads(out)
    assert "total_lines" in payload


def test_report_json_lines_have_fields():
    result = extract(_JSON_LINES)
    out = report_extract_json(result)
    payload = json.loads(out)
    first = payload["lines"][0]
    assert "fields" in first
    assert "raw" in first


def test_get_extract_reporter_text():
    reporter = get_extract_reporter("text")
    result = extract(_KV_LINES)
    assert isinstance(reporter(result), str)


def test_get_extract_reporter_json():
    reporter = get_extract_reporter("json")
    result = extract(_KV_LINES)
    payload = json.loads(reporter(result))
    assert payload["total_lines"] == 3


def test_get_extract_reporter_default_is_text():
    assert get_extract_reporter() is report_extract_text
