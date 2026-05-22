"""Tests for logslice.tail."""

from __future__ import annotations

import os
import threading
import time

import pytest

from logslice.tail import TailResult, follow, tail_lines


@pytest.fixture()
def log_path(tmp_path):
    p = tmp_path / "app.log"
    lines = [f"2024-01-01 00:00:{i:02d} INFO line {i}" for i in range(30)]
    p.write_text("\n".join(lines) + "\n")
    return str(p)


def test_tail_lines_returns_tail_result(log_path):
    result = tail_lines(log_path, n=5)
    assert isinstance(result, TailResult)


def test_tail_lines_correct_count(log_path):
    result = tail_lines(log_path, n=10)
    assert len(result.lines) == 10


def test_tail_lines_last_line_is_last(log_path):
    result = tail_lines(log_path, n=3)
    assert "line 29" in result.lines[-1]


def test_tail_lines_n_larger_than_file(log_path):
    result = tail_lines(log_path, n=200)
    assert len(result.lines) == 30


def test_tail_lines_n_zero_returns_empty(log_path):
    result = tail_lines(log_path, n=0)
    assert result.lines == []
    assert result.total_read == 0


def test_tail_lines_total_read_positive(log_path):
    result = tail_lines(log_path, n=5)
    assert result.total_read > 0


def test_follow_yields_new_lines(tmp_path):
    p = tmp_path / "live.log"
    p.write_text("")

    results: list[str] = []

    def _write():
        time.sleep(0.1)
        with open(str(p), "a") as fh:
            for i in range(3):
                fh.write(f"2024-01-01 00:00:0{i} INFO msg {i}\n")
                fh.flush()
                time.sleep(0.05)

    writer = threading.Thread(target=_write, daemon=True)
    writer.start()

    for line in follow(str(p), poll_interval=0.05, start_from_end=True, timeout=1.5):
        results.append(line)
        if len(results) >= 3:
            break

    writer.join(timeout=2)
    assert len(results) == 3
    assert "msg 0" in results[0]


def test_follow_timeout_stops_iteration(tmp_path):
    p = tmp_path / "static.log"
    p.write_text("existing line\n")

    collected = list(follow(str(p), poll_interval=0.05, start_from_end=True, timeout=0.3))
    assert collected == []
