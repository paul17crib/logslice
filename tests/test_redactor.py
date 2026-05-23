"""Tests for logslice.redactor."""

import pytest

from logslice.redactor import (
    REDACT_PLACEHOLDER,
    RedactResult,
    redact,
    iter_redacted,
)


# ---------------------------------------------------------------------------
# redact() return type
# ---------------------------------------------------------------------------

def test_redact_returns_redact_result():
    result = redact([])
    assert isinstance(result, RedactResult)


def test_redact_empty_input():
    result = redact([])
    assert result.lines == []
    assert result.total_lines == 0
    assert result.redacted_lines == 0
    assert result.redaction_count == 0


def test_redact_no_patterns_unchanged():
    lines = ["hello world", "foo bar"]
    result = redact(lines)
    assert result.lines == lines
    assert result.redacted_lines == 0


# ---------------------------------------------------------------------------
# preset: ipv4
# ---------------------------------------------------------------------------

def test_redact_preset_ipv4_masks_address():
    lines = ["Connected from 192.168.1.1 at port 443"]
    result = redact(lines, presets=["ipv4"])
    assert "192.168.1.1" not in result.lines[0]
    assert REDACT_PLACEHOLDER in result.lines[0]


def test_redact_preset_ipv4_counts_correctly():
    lines = ["src=10.0.0.1 dst=10.0.0.2"]
    result = redact(lines, presets=["ipv4"])
    assert result.redaction_count == 2
    assert result.redacted_lines == 1


# ---------------------------------------------------------------------------
# preset: email
# ---------------------------------------------------------------------------

def test_redact_preset_email_masks_address():
    lines = ["User user@example.com logged in"]
    result = redact(lines, presets=["email"])
    assert "user@example.com" not in result.lines[0]
    assert REDACT_PLACEHOLDER in result.lines[0]


# ---------------------------------------------------------------------------
# custom pattern
# ---------------------------------------------------------------------------

def test_redact_custom_pattern_applied():
    lines = ["order_id=ABC-12345 processed"]
    result = redact(lines, patterns=[r"ABC-\d+"])
    assert "ABC-12345" not in result.lines[0]
    assert result.redaction_count == 1


def test_redact_custom_placeholder():
    lines = ["ip=1.2.3.4"]
    result = redact(lines, presets=["ipv4"], placeholder="***")
    assert "***" in result.lines[0]
    assert REDACT_PLACEHOLDER not in result.lines[0]


# ---------------------------------------------------------------------------
# redaction_ratio
# ---------------------------------------------------------------------------

def test_redaction_ratio_zero_when_no_matches():
    result = redact(["clean line", "another clean"])
    assert result.redaction_ratio == 0.0


def test_redaction_ratio_correct():
    lines = ["ip=1.2.3.4", "clean", "ip=5.6.7.8"]
    result = redact(lines, presets=["ipv4"])
    assert result.redaction_ratio == pytest.approx(2 / 3)


# ---------------------------------------------------------------------------
# unknown preset raises
# ---------------------------------------------------------------------------

def test_unknown_preset_raises_value_error():
    with pytest.raises(ValueError, match="Unknown preset"):
        redact(["line"], presets=["nonexistent"])


# ---------------------------------------------------------------------------
# iter_redacted
# ---------------------------------------------------------------------------

def test_iter_redacted_yields_tuples():
    lines = ["user@test.com", "no match here"]
    results = list(iter_redacted(lines, presets=["email"]))
    assert len(results) == 2
    redacted_line, count = results[0]
    assert count == 1
    _, count2 = results[1]
    assert count2 == 0


def test_multiple_presets_combined():
    lines = ["email=admin@site.org ip=10.10.10.1"]
    result = redact(lines, presets=["email", "ipv4"])
    assert result.redaction_count == 2
    assert "admin@site.org" not in result.lines[0]
    assert "10.10.10.1" not in result.lines[0]
