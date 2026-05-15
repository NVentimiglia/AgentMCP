"""Cross-platform PID lockfile + cooldown stamp for skills-mcp analyze.

Two files live under ``state/``:
  analyze.lock  — PID of a currently-running analyze process (deleted on finish).
  analyze.stamp — Unix timestamp of the last completed run (for cooldown).
"""

from __future__ import annotations

import os
import time
from pathlib import Path

LOCK_FILENAME = "analyze.lock"
STAMP_FILENAME = "analyze.stamp"
DEFAULT_COOLDOWN_SECONDS = 60 * 60  # 1 hour


def _pid_alive(pid: int) -> bool:
    """Return True if a process with this PID is currently running."""
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True   # process exists; we just lack permission to signal it
    except OSError:
        return False  # process does not exist


class AnalyzeLock:
    """File-based exclusive lock with per-turn cooldown.

    Usage::

        lock = AnalyzeLock(state_dir)
        ok, reason = lock.try_acquire()
        if not ok:
            print(f"skipping: {reason}")
            return 0
        try:
            ...do work...
            lock.stamp()   # record successful completion
        finally:
            lock.release()
    """

    def __init__(self, state_dir: Path, cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS) -> None:
        self._state_dir = state_dir
        self._cooldown = cooldown_seconds
        self._lock_path = state_dir / LOCK_FILENAME
        self._stamp_path = state_dir / STAMP_FILENAME
        self._acquired = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def try_acquire(self) -> tuple[bool, str]:
        """Try to acquire the lock.

        Returns ``(True, "")`` on success or ``(False, reason)`` when skipped.
        Caller MUST call ``release()`` (or use as context manager) after acquiring.
        """
        self._state_dir.mkdir(parents=True, exist_ok=True)

        # 1. Cooldown: skip if last run was recent.
        remaining = self._cooldown_remaining()
        if remaining > 0:
            mins = remaining // 60
            secs = remaining % 60
            return False, f"cooldown: next run in {mins}m {secs}s"

        # 2. Existing lock: skip if another process is running.
        if self._lock_path.is_file():
            try:
                pid = int(self._lock_path.read_text(encoding="utf-8").strip())
                if _pid_alive(pid):
                    return False, f"already running (pid {pid})"
            except (ValueError, OSError):
                pass  # stale lock — take it over

        # 3. Acquire: write our PID.
        try:
            self._lock_path.write_text(str(os.getpid()), encoding="utf-8")
            self._acquired = True
            return True, ""
        except OSError as exc:
            return False, f"could not write lock: {exc}"

    def stamp(self) -> None:
        """Record the current time as a successful-run timestamp."""
        try:
            self._stamp_path.write_text(str(int(time.time())), encoding="utf-8")
        except OSError:
            pass

    def release(self) -> None:
        """Delete the lockfile if we hold it."""
        if self._acquired:
            try:
                self._lock_path.unlink(missing_ok=True)
            except OSError:
                pass
            self._acquired = False

    def __enter__(self) -> "AnalyzeLock":
        return self

    def __exit__(self, *_: object) -> None:
        self.release()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _cooldown_remaining(self) -> int:
        """Seconds left in cooldown, or 0 if no cooldown applies."""
        if not self._stamp_path.is_file():
            return 0
        try:
            last = int(self._stamp_path.read_text(encoding="utf-8").strip())
            elapsed = int(time.time()) - last
            remaining = self._cooldown - elapsed
            return max(0, remaining)
        except (ValueError, OSError):
            return 0
