"""Application directory paths using platformdirs."""

from pathlib import Path

from platformdirs import PlatformDirs

from audiokeep import __app_name__

_dirs = PlatformDirs(appname=__app_name__.lower(), appauthor=False)


def config_dir() -> Path:
    """User config directory (e.g. %APPDATA%/audiokeep on Windows)."""
    return Path(_dirs.user_config_dir)


def log_dir() -> Path:
    """User log directory."""
    return Path(_dirs.user_log_dir)


def config_file() -> Path:
    """Full path to settings.json."""
    return config_dir() / "settings.json"
