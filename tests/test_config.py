"""Tests for config models and store."""

import json
from pathlib import Path

import pytest

from audiokeep.config.models import MAX_LEVEL_DB, MIN_LEVEL_DB, AppSettings
from audiokeep.config.store import SettingsStore


class TestAppSettings:
    def test_defaults(self):
        s = AppSettings()
        assert s.keep_alive_level_db == -70.0
        assert s.sample_rate == 48000
        assert s.channels == 2
        assert s.auto_start is False
        assert s.start_minimized is True
        assert s.output_device_name is None

    def test_level_clamping(self):
        s = AppSettings(keep_alive_level_db=-100.0)
        assert s.keep_alive_level_db == MIN_LEVEL_DB

        s2 = AppSettings(keep_alive_level_db=-40.0)
        assert s2.keep_alive_level_db == MAX_LEVEL_DB

    def test_valid_range(self):
        for db in [-90, -80, -70, -60, -50]:
            s = AppSettings(keep_alive_level_db=float(db))
            assert s.keep_alive_level_db == float(db)

    def test_db_to_amplitude(self):
        s = AppSettings(keep_alive_level_db=-60.0)
        amp = s.db_to_amplitude()
        assert abs(amp - 0.001) < 1e-6

    def test_db_to_amplitude_at_max(self):
        s = AppSettings(keep_alive_level_db=MAX_LEVEL_DB)
        expected = 10.0 ** (MAX_LEVEL_DB / 20.0)
        assert s.db_to_amplitude() == pytest.approx(expected)

    def test_clamping_above_max(self):
        s = AppSettings(keep_alive_level_db=0.0)
        assert s.keep_alive_level_db == MAX_LEVEL_DB

    def test_model_dump_roundtrip(self):
        s = AppSettings(keep_alive_level_db=-65.0, auto_start=True)
        data = s.model_dump()
        s2 = AppSettings(**data)
        assert s2.keep_alive_level_db == -65.0
        assert s2.auto_start is True


class TestSettingsStore:
    def test_load_missing_file(self, tmp_path: Path):
        store = SettingsStore(tmp_path / "nonexistent.json")
        assert store.settings.keep_alive_level_db == -70.0

    def test_save_and_reload(self, tmp_path: Path):
        path = tmp_path / "settings.json"
        store = SettingsStore(path)
        store.update(keep_alive_level_db=-60.0)

        store2 = SettingsStore(path)
        assert store2.settings.keep_alive_level_db == -60.0

    def test_corrupt_config_backup(self, tmp_path: Path):
        path = tmp_path / "settings.json"
        path.write_text("{bad json!!!", encoding="utf-8")

        store = SettingsStore(path)
        assert store.settings.keep_alive_level_db == -70.0
        # Should have created a backup
        backups = list(tmp_path.glob("*.bak.*"))
        assert len(backups) == 1

    def test_reset(self, tmp_path: Path):
        store = SettingsStore(tmp_path / "settings.json")
        store.update(keep_alive_level_db=-55.0, auto_start=True)
        store.reset()
        assert store.settings.keep_alive_level_db == -70.0
        assert store.settings.auto_start is False
