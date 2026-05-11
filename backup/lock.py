import fcntl
import os
from pathlib import Path
from typing import Optional

from loguru import logger


class FileLock:
    """Exclusive file lock to prevent concurrent backup runs."""

    def __init__(self, lock_path: Path):
        self._lock_path = lock_path
        self._fd: Optional[int] = None
        self._log = logger.bind(phase="lock")

    def __enter__(self) -> "FileLock":
        self._fd = os.open(str(self._lock_path), os.O_CREAT | os.O_RDWR, 0o644)
        try:
            fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(self._fd)
            self._fd = None
            raise LockError(
                f"Another backup instance is running (lock held at {self._lock_path})"
            )
        # Write PID to lock file for debugging
        os.ftruncate(self._fd, 0)
        os.write(self._fd, str(os.getpid()).encode())
        self._log.debug(f"Lock acquired: {self._lock_path}")
        return self

    def __exit__(self, *args: object) -> None:
        if self._fd is not None:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
            os.close(self._fd)
            self._fd = None
        try:
            self._lock_path.unlink(missing_ok=True)
        except OSError:
            pass
        self._log.debug(f"Lock released: {self._lock_path}")


class LockError(Exception):
    """Lock contention — another instance is running."""
