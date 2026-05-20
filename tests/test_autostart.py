"""Tests for autostart registry logic (mocked on non-Windows or CI)."""

import sys
from unittest.mock import MagicMock, patch

import pytest


# Only import the module if we're on Windows; otherwise mock it.
@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only")
class TestAutoStart:
    @patch("audiokeep.system.autostart.winreg")
    def test_is_auto_start_enabled_true(self, mock_winreg):
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value.__enter__ = MagicMock(return_value=mock_key)
        mock_winreg.OpenKey.return_value.__exit__ = MagicMock(return_value=False)
        mock_winreg.KEY_READ = 0x20019

        from audiokeep.system.autostart import is_auto_start_enabled
        assert is_auto_start_enabled() is True

    @patch("audiokeep.system.autostart.winreg")
    def test_is_auto_start_enabled_false(self, mock_winreg):
        mock_winreg.OpenKey.side_effect = FileNotFoundError
        mock_winreg.KEY_READ = 0x20019

        from audiokeep.system.autostart import is_auto_start_enabled
        assert is_auto_start_enabled() is False

    @patch("audiokeep.system.autostart.winreg")
    def test_set_auto_start_enable(self, mock_winreg):
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value.__enter__ = MagicMock(return_value=mock_key)
        mock_winreg.OpenKey.return_value.__exit__ = MagicMock(return_value=False)
        mock_winreg.KEY_SET_VALUE = 0x20002
        mock_winreg.REG_SZ = 1

        from audiokeep.system.autostart import set_auto_start
        set_auto_start(True)
        mock_winreg.SetValueEx.assert_called_once()

    @patch("audiokeep.system.autostart.winreg")
    def test_set_auto_start_disable(self, mock_winreg):
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value.__enter__ = MagicMock(return_value=mock_key)
        mock_winreg.OpenKey.return_value.__exit__ = MagicMock(return_value=False)
        mock_winreg.KEY_SET_VALUE = 0x20002

        from audiokeep.system.autostart import set_auto_start
        set_auto_start(False)
        mock_winreg.DeleteValue.assert_called_once()
