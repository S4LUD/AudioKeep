"""Single-instance guard using a Windows named mutex."""

import ctypes
import logging
import sys

logger = logging.getLogger(__name__)

_MUTEX_NAME = "Global\\AudioKeep_SingleInstance"


class SingleInstance:
    """Ensures only one instance of AudioKeep runs at a time using a named mutex."""

    def __init__(self) -> None:
        self._handle = None

    def acquire(self) -> bool:
        """Try to acquire the mutex. Returns True if this is the only instance."""
        if sys.platform != "win32":
            return self._acquire_fallback()

        kernel32 = ctypes.windll.kernel32
        # CreateMutex returns existing handle if mutex already exists
        handle = kernel32.CreateMutexW(None, True, _MUTEX_NAME)
        if not handle:
            logger.error("Failed to create mutex.")
            return False

        # ERROR_ALREADY_EXISTS (183) means another instance holds it
        last_error = kernel32.GetLastError()
        if last_error == 183:
            kernel32.CloseHandle(handle)
            logger.error("Another AudioKeep instance is already running.")
            return False

        self._handle = handle
        return True

    def release(self) -> None:
        """Release the mutex."""
        if self._handle:
            ctypes.windll.kernel32.CloseHandle(self._handle)
            self._handle = None

    def _acquire_fallback(self) -> bool:
        """Fallback for non-Windows using a lock file."""
        import os
        from pathlib import Path

        lock_path = Path.home() / ".audiokeep.lock"
        if lock_path.exists():
            try:
                pid = int(lock_path.read_text().strip())
                os.kill(pid, 0)
                logger.error("Another AudioKeep instance is already running.")
                return False
            except (ValueError, OSError):
                pass
        try:
            lock_path.write_text(str(os.getpid()))
            self._lock_path = lock_path
            return True
        except OSError:
            return False
