"""Tests for AnalyzeLock (lockfile + cooldown)."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from skills_mcp.lockfile import AnalyzeLock, LOCK_FILENAME, STAMP_FILENAME


def test_first_acquire_succeeds(tmp_path: Path) -> None:
    lock = AnalyzeLock(tmp_path)
    ok, reason = lock.try_acquire()
    assert ok
    assert reason == ""
    lock.release()


def test_release_removes_lockfile(tmp_path: Path) -> None:
    lock = AnalyzeLock(tmp_path)
    lock.try_acquire()
    lock.release()
    assert not (tmp_path / LOCK_FILENAME).is_file()


def test_second_acquire_blocked_while_held(tmp_path: Path) -> None:
    lock1 = AnalyzeLock(tmp_path)
    lock1.try_acquire()

    lock2 = AnalyzeLock(tmp_path)
    ok, reason = lock2.try_acquire()
    assert not ok
    assert "already running" in reason

    lock1.release()


def test_stale_lock_overwritten(tmp_path: Path) -> None:
    # Write a lockfile with a PID that cannot possibly be running.
    lock_path = tmp_path / LOCK_FILENAME
    lock_path.write_text("999999999", encoding="utf-8")  # unreachable PID

    lock = AnalyzeLock(tmp_path)
    ok, _ = lock.try_acquire()
    assert ok
    assert lock_path.read_text(encoding="utf-8").strip() == str(os.getpid())
    lock.release()


def test_cooldown_blocks_reacquire(tmp_path: Path) -> None:
    lock = AnalyzeLock(tmp_path, cooldown_seconds=3600)
    lock.try_acquire()
    lock.stamp()
    lock.release()

    lock2 = AnalyzeLock(tmp_path, cooldown_seconds=3600)
    ok, reason = lock2.try_acquire()
    assert not ok
    assert "cooldown" in reason


def test_cooldown_zero_allows_reacquire(tmp_path: Path) -> None:
    lock = AnalyzeLock(tmp_path, cooldown_seconds=0)
    lock.try_acquire()
    lock.stamp()
    lock.release()

    lock2 = AnalyzeLock(tmp_path, cooldown_seconds=0)
    ok, _ = lock2.try_acquire()
    assert ok
    lock2.release()


def test_stamp_written_on_success(tmp_path: Path) -> None:
    lock = AnalyzeLock(tmp_path)
    lock.try_acquire()
    before = int(time.time())
    lock.stamp()
    lock.release()

    stamp_path = tmp_path / STAMP_FILENAME
    assert stamp_path.is_file()
    written = int(stamp_path.read_text(encoding="utf-8").strip())
    assert written >= before


def test_expired_cooldown_allows_acquire(tmp_path: Path) -> None:
    stamp_path = tmp_path / STAMP_FILENAME
    # Write a stamp far in the past.
    stamp_path.write_text(str(int(time.time()) - 7200), encoding="utf-8")

    lock = AnalyzeLock(tmp_path, cooldown_seconds=3600)
    ok, _ = lock.try_acquire()
    assert ok
    lock.release()


def test_context_manager_releases_on_exit(tmp_path: Path) -> None:
    lock = AnalyzeLock(tmp_path)
    with lock:
        lock.try_acquire()
        assert (tmp_path / LOCK_FILENAME).is_file()
    assert not (tmp_path / LOCK_FILENAME).is_file()
