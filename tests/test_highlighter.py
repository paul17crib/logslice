"""Tests for logslice.highlighter."""

import pytest

from logslice.highlighter import (
    HighlightResult,
    get_highlighter,
    highlight_ansi,
    highlight_plain,
    ANSI_YELLOW,
    ANSI_RED,
    ANSI_RESET,
)


LINES = [
    "2024-01-01 00:00:01 INFO  server started",
    "2024-01-01 00:00:02 WARN  disk usage high",
    "2024-01-01 00:00:03 ERROR connection refused",
    "2024-01-01 00:00:04 INFO  all good",
]


def test_highlight_plain_marks_matching_lines():
    result = highlight_plain(LINES, ["WARN", "ERROR"])
    assert result.lines[0] == LINES[0]  # no match
    assert result.lines[1].startswith(">>> ")
    assert result.lines[2].startswith(">>> ")
    assert result.lines[3] == LINES[3]  # no match


def test_highlight_plain_matched_count():
    result = highlight_plain(LINES, ["ERROR"])
    assert result.matched_count == 1


def test_highlight_plain_custom_marker():
    result = highlight_plain(LINES, ["INFO"], marker="!!")
    assert result.lines[0].startswith("!! ")


def test_highlight_plain_case_insensitive_default():
    result = highlight_plain(LINES, ["warn"])
    assert result.matched_count == 1


def test_highlight_plain_case_sensitive():
    result = highlight_plain(LINES, ["warn"], case_sensitive=True)
    assert result.matched_count == 0  # file uses 'WARN'


def test_highlight_ansi_returns_highlight_result():
    result = highlight_ansi(LINES, ["ERROR"])
    assert isinstance(result, HighlightResult)


def test_highlight_ansi_error_line_uses_red():
    result = highlight_ansi(LINES, ["ERROR"])
    assert ANSI_RED in result.lines[2]
    assert ANSI_RESET in result.lines[2]


def test_highlight_ansi_warn_line_uses_yellow():
    result = highlight_ansi(LINES, ["WARN"])
    assert ANSI_YELLOW in result.lines[1]


def test_highlight_ansi_non_matching_lines_unchanged():
    result = highlight_ansi(LINES, ["ERROR"])
    assert result.lines[0] == LINES[0]
    assert result.lines[3] == LINES[3]


def test_highlight_ansi_matched_count():
    result = highlight_ansi(LINES, ["INFO"])
    assert result.matched_count == 2


def test_highlight_empty_input():
    result = highlight_plain([], ["ERROR"])
    assert result.lines == []
    assert result.matched_count == 0


def test_highlight_no_keywords_raises():
    with pytest.raises(ValueError):
        highlight_plain(LINES, [])


def test_get_highlighter_ansi():
    fn = get_highlighter("ansi")
    assert fn is highlight_ansi


def test_get_highlighter_plain():
    fn = get_highlighter("plain")
    assert fn is highlight_plain


def test_get_highlighter_unknown_raises():
    with pytest.raises(ValueError, match="Unknown highlight mode"):
        get_highlighter("html")
