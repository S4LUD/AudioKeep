"""Windows registry-based auto-start (Current User, no admin required)."""

import logging
import sys
import winreg
from pathlib import Path

logger = logging.getLogger(__name__)

_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_APP_NAME = "AudioKeep"


def _get_exe_path() -> str:
    """Return the path to the running executable or python script."""
    if getattr(sys, "frozen", False):
        return str(Path(sys.executable))
    return f'"{sys.executable}" -m audiokeep'


def is_auto_start_enabled() -> bool:
    """Check if the app is registered for auto-start."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, _APP_NAME)
            return True
        return False
    except OSError:
        return False


def set_auto_start(enabled: bool) -> None:
    """Enable or disable auto-start via HKCU Run key."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                path = _get_exe_path()
                winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, path)
                logger.info("Auto-start enabled: %s", path)
            else:
                try:
                    winreg.DeleteValue(key, _APP_NAME)
                    logger.info("Auto-start disabled.")
                except FileNotFoundError:
                    pass
    except OSError as exc:
        logger.error("Failed to update auto-start registry: %s", exc)
