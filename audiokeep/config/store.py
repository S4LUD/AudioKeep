"""Persistent settings store backed by JSON."""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path

from .models import AppSettings

logger = logging.getLogger(__name__)


class SettingsStore:
    """Loads and saves AppSettings to a JSON file."""

    def __init__(self, config_path: Path) -> None:
        self._path = config_path
        self._settings = self._load()

    @property
    def settings(self) -> AppSettings:
        return self._settings

    @property
    def path(self) -> Path:
        return self._path

    def update(self, **kwargs: object) -> AppSettings:
        """Create a new validated AppSettings with merged values and persist it."""
        data = self._settings.model_dump()
        data.update(kwargs)
        self._settings = AppSettings(**data)
        self._save()
        return self._settings

    def replace(self, settings: AppSettings) -> None:
        """Replace the current settings entirely and persist."""
        self._settings = settings
        self._save()

    def reset(self) -> AppSettings:
        """Reset to defaults and persist."""
        self._settings = AppSettings()
        self._save()
        return self._settings

    def _load(self) -> AppSettings:
        if not self._path.exists():
            logger.info("No config file found; using defaults.")
            return AppSettings()
        try:
            raw = self._path.read_text(encoding="utf-8")
            data = json.loads(raw)
            settings = AppSettings(**data)
            logger.info("Loaded config from %s", self._path)
            return settings
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Corrupt config at %s: %s. Backing up and resetting.", self._path, exc)
            self._backup_corrupt()
            return AppSettings()
        except Exception as exc:
            logger.error("Unexpected error loading config: %s", exc)
            return AppSettings()

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                self._settings.model_dump_json(indent=2),
                encoding="utf-8",
            )
            logger.debug("Saved config to %s", self._path)
        except OSError as exc:
            logger.error("Failed to save config: %s", exc)

    def _backup_corrupt(self) -> None:
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = self._path.with_suffix(f".bak.{ts}")
            shutil.copy2(self._path, backup)
            logger.info("Backed up corrupt config to %s", backup)
        except OSError as exc:
            logger.warning("Could not back up corrupt config: %s", exc)
