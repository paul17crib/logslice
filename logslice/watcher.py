"""File-system watcher that triggers a callback whenever a log file grows."""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional


@dataclass
class WatcherState:
    path: str
    last_size: int = 0
    events: int = 0
    running: bool = False
    errors: List[str] = field(default_factory=list)


class LogWatcher:
    """Poll *path* and invoke *callback* with new content when the file grows.

    Parameters
    ----------
    path:          Path to the file to watch.
    callback:      Called with a list of new lines each time growth is detected.
    poll_interval: Seconds between stat checks.
    """

    def __init__(
        self,
        path: str,
        callback: Callable[[List[str]], None],
        poll_interval: float = 0.5,
    ) -> None:
        self.path = path
        self.callback = callback
        self.poll_interval = poll_interval
        self._state = WatcherState(path=path)
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    @property
    def state(self) -> WatcherState:
        return self._state

    def start(self) -> None:
        """Start the background polling thread."""
        if self._state.running:
            return
        self._stop_event.clear()
        self._state.running = True
        try:
            self._state.last_size = os.path.getsize(self.path)
        except OSError:
            self._state.last_size = 0
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        """Signal the background thread to stop and wait for it."""
        self._stop_event.set()
        self._state.running = False
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                current_size = os.path.getsize(self.path)
                if current_size > self._state.last_size:
                    new_lines = self._read_new(self._state.last_size, current_size)
                    self._state.last_size = current_size
                    self._state.events += 1
                    if new_lines:
                        self.callback(new_lines)
            except OSError as exc:
                self._state.errors.append(str(exc))
            self._stop_event.wait(self.poll_interval)

    def _read_new(self, old_size: int, new_size: int) -> List[str]:
        try:
            with open(self.path, "r", encoding="utf-8", errors="replace") as fh:
                fh.seek(old_size)
                data = fh.read(new_size - old_size)
            return [ln for ln in data.splitlines() if ln]
        except OSError:
            return []
