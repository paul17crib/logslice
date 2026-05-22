"""Integration tests combining tail and watcher."""

from __future__ import annotations

import time

import pytest

from logslice.tail import tail_lines
from logslice.watcher import LogWatcher


@pytest.fixture()
def growing_log(tmp_path):
    p = tmp_path / "growing.log"
    lines = [f"2024-01-01 00:00:{i:02d} INFO seed {i}" for i in range(10)]
    p.write_text("\n".join(lines) + "\n")
    return p


def test_tail_then_watch_sees_new_content(growing_log):
    """tail_lines captures existing content; watcher captures appended content."""
    initial = tail_lines(str(growing_log), n=5)
    assert len(initial.lines) == 5
    assert "seed 9" in initial.lines[-1]

    seen: list[str] = []

    def _cb(lines):
        seen.extend(lines)

    watcher = LogWatcher(str(growing_log), callback=_cb, poll_interval=0.05)
    watcher.start()
    time.sleep(0.1)

    with open(str(growing_log), "a") as fh:
        fh.write("2024-01-01 00:00:10 INFO appended line\n")

    deadline = time.monotonic() + 2.0
    while not seen and time.monotonic() < deadline:
        time.sleep(0.05)

    watcher.stop()
    assert any("appended line" in ln for ln in seen)


def test_watcher_accumulates_multiple_batches(growing_log):
    batches: list[list[str]] = []

    watcher = LogWatcher(str(growing_log), callback=lambda ls: batches.append(ls), poll_interval=0.05)
    watcher.start()
    time.sleep(0.1)

    for i in range(3):
        with open(str(growing_log), "a") as fh:
            fh.write(f"2024-01-01 00:01:{i:02d} INFO batch {i}\n")
        time.sleep(0.15)

    watcher.stop()
    all_lines = [ln for b in batches for ln in b]
    assert sum(1 for ln in all_lines if "batch" in ln) == 3
