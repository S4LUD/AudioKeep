"""Application controller: wires together all subsystems."""

import logging
import threading
import tkinter as tk
from typing import Callable

from audiokeep.audio.engine import AudioEngine
from audiokeep.config.models import AppSettings
from audiokeep.config.store import SettingsStore
from audiokeep.system.autostart import set_auto_start
from audiokeep.ui.settings_window import SettingsWindow
from audiokeep.ui.tray import TrayIcon
from audiokeep.utils.thread_safe import RunState

logger = logging.getLogger(__name__)


class App:
    """Top-level application controller.

    The main thread owns a hidden Tk root and runs its event loop.
    All UI work is dispatched to the main thread via ``_schedule()``.
    """

    def __init__(self, store: SettingsStore) -> None:
        self._store = store
        self._engine = AudioEngine(store.settings)
        self._tray = TrayIcon(self)
        self._settings_win: SettingsWindow | None = None
        self._settings_lock = threading.Lock()
        self._root: tk.Tk | None = None

    # --- Public accessors ---

    @property
    def store(self) -> SettingsStore:
        return self._store

    @property
    def engine(self) -> AudioEngine:
        return self._engine

    @property
    def settings(self) -> AppSettings:
        return self._store.settings

    # --- Lifecycle ---

    def run(self) -> None:
        """Start the application. Blocks the main thread with a tkinter event loop."""
        logger.info("AudioKeep starting.")

        self._engine.set_error_callback(self._on_engine_error)
        self._engine.start()

        # Hidden root — owns the Tk event loop on the main thread
        self._root = tk.Tk()
        self._root.withdraw()

        self._tray.start()
        self._tray.update_tooltip("AudioKeep - Running")

        # Poll for shutdown requests every 200ms
        self._root.after(200, self._poll_shutdown)

        # This blocks the main thread and pumps the Tk event loop
        self._root.mainloop()

        logger.info("AudioKeep shutting down.")
        self._engine.stop()
        self._tray.stop()
        logger.info("AudioKeep stopped.")

    def shutdown(self) -> None:
        """Request a clean shutdown. Safe to call from any thread."""
        logger.info("Shutdown requested.")
        self._schedule(self._do_shutdown)

    # --- Actions (called from tray thread, executed on main thread) ---

    def change_device(self, device_name: str) -> None:
        """Switch the output device and restart the stream."""
        self._store.update(output_device_name=device_name)
        was_running = self._engine.is_running
        self._engine.stop()
        self._engine.update_settings(self._store.settings)
        if was_running:
            self._engine.start()
        logger.info("Device changed to: %s", device_name)

    def open_settings(self) -> None:
        """Open the settings window. Safe to call from any thread."""
        self._schedule(self._do_open_settings)

    # --- Internal ---

    def _schedule(self, fn: Callable[[], None]) -> None:
        """Schedule ``fn`` to run on the main (Tk) thread."""
        if self._root is not None:
            self._root.after(0, fn)

    def _do_open_settings(self) -> None:
        """Runs on the main thread."""
        with self._settings_lock:
            if self._settings_win is None:
                self._settings_win = SettingsWindow(self)
            self._settings_win.show()

    def _do_shutdown(self) -> None:
        """Runs on the main thread — breaks the mainloop."""
        if self._root is not None:
            self._root.quit()

    def _poll_shutdown(self) -> None:
        """Keep the periodic check alive while the app is running."""
        if self._root is not None:
            self._root.after(200, self._poll_shutdown)

    def _on_engine_error(self, message: str) -> None:
        logger.error("Engine error callback: %s", message)
