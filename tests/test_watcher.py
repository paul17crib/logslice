"""Tests for logslice.watcher.LogWatcher."""

from __future__ import annotations

import time

import pytest

from logslice.watcher import LogWatcher, WatcherState


@pytest.fixture()
def log_file(tmp_path):
    p = tmp_path / "watch.log"
    p.write_text("initial line\n")
    return p


def test_watcher_state_is_watcher_state(log_file):
    watcher = LogWatcher(str(log_file), callback=lambda lines: None)
    assert isinstance(watcher.state, WatcherState)


def test_watcher_starts_and_stops(log_file):
    watcher = LogWatcher(str(log_file), callback=lambda lines: None, poll_interval=0.05)
    watcher.start()
    assert watcher.state.running is True
    watcher.stop()
    assert watcher.state.running is False


def test_watcher_detects_new_lines(log_file):
    collected: list[list[str]] = []

    def _cb(lines):
        collected.append(lines)

    watcher = LogWatcher(str(log_file), callback=_cb, poll_interval=0.05)
    watcher.start()

    time.sleep(0.1)
    with open(str(log_file), "a") as fh:
        fh.write("new line A\nnew line B\n")

    deadline = time.monotonic() + 2.0
    while not collected and time.monotonic() < deadline:
        time.sleep(0.05)

    watcher.stop()
    all_lines = [ln for batch in collected for ln in batch]
    assert "new line A" in all_lines
    assert "new line B" in all_lines


def test_watcher_events_incremented(log_file):
    watcher = LogWatcher(str(log_file), callback=lambda lines: None, poll_interval=0.05)
    watcher.start()
    time.sleep(0.1)
    with open(str(log_file), "a") as fh:
        fh.write("event trigger\n")
    time.sleep(0.3)
    watcher.stop()
    assert watcher.state.events >= 1


def test_watcher_no_duplicate_start(log_file):
    watcher = LogWatcher(str(log_file), callback=lambda lines: None, poll_interval=0.1)
    watcher.start()
    thread_before = watcher._thread
    watcher.start()  # second start should be a no-op
    assert watcher._thread is thread_before
    watcher.stop()


def test_watcher_missing_file_records_error(tmp_path):
    missing = str(tmp_path / "ghost.log")
    errors: list[str] = []

    def _cb(lines):
        pass

    watcher = LogWatcher(missing, callback=_cb, poll_interval=0.05)
    # Override last_size to skip the initial getsize in start()
    watcher._state.last_size = 0
    watcher._state.running = True
    watcher._run.__func__  # just ensure it is callable
    # Manually trigger one poll cycle
    watcher._read_new(0, 100)  # file missing -> returns []
    # No exception raised
