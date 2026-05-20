"""System tray icon and menu."""

import logging
import sys
import threading
from pathlib import Path
from typing import TYPE_CHECKING

import pystray
from PIL import Image, ImageDraw

if TYPE_CHECKING:
    from audiokeep.app import App

logger = logging.getLogger(__name__)

_ICON_SIZE = 64


def _find_icon_path() -> Path | None:
    """Locate the app icon PNG."""
    if getattr(sys, "frozen", False):
        # PyInstaller --onefile extracts to _MEIPASS temp dir
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        base = Path(__file__).resolve().parent.parent.parent
    for name in ("audio_keep_icon.png", "assets/audio_keep_icon.png"):
        p = base / name
        if p.exists():
            return p
    return None


def _load_icon_image() -> Image.Image:
    """Load the app icon, or fall back to a procedural one."""
    path = _find_icon_path()
    if path:
        img = Image.open(path).convert("RGBA")
        return img.resize((_ICON_SIZE, _ICON_SIZE), Image.LANCZOS)
    # Fallback
    img = Image.new("RGBA", (_ICON_SIZE, _ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([8, 8, _ICON_SIZE - 8, _ICON_SIZE - 8], fill=(0, 180, 120))
    draw.ellipse([20, 20, _ICON_SIZE - 20, _ICON_SIZE - 20], fill=(255, 255, 255, 200))
    return img


def _create_paused_icon(icon: Image.Image) -> Image.Image:
    """Desaturate the icon for the paused state."""
    return icon.convert("L").convert("RGBA")


class TrayIcon:
    """Manages the system tray icon and its menu."""

    def __init__(self, app: "App") -> None:
        self._app = app
        self._icon: pystray.Icon | None = None
        self._thread: threading.Thread | None = None
        self._paused = False
        self._icon_image = _load_icon_image()

    def start(self) -> None:
        self._icon = pystray.Icon(
            "AudioKeep",
            self._icon_image,
            "AudioKeep - Running",
            self._build_menu(),
        )
        self._thread = threading.Thread(target=self._icon.run, daemon=True, name="tray")
        self._thread.start()
        logger.info("Tray icon started.")

    def stop(self) -> None:
        if self._icon:
            self._icon.stop()
            self._icon = None
        logger.info("Tray icon stopped.")

    def update_tooltip(self, text: str) -> None:
        if self._icon:
            self._icon.title = text

    def update_icon(self, running: bool) -> None:
        if self._icon:
            self._icon.icon = self._icon_image if running else _create_paused_icon(self._icon_image)

    def _rebuild_menu(self) -> None:
        if self._icon:
            self._icon.menu = self._build_menu()

    def _build_menu(self) -> pystray.Menu:
        status_text = "Paused" if self._paused else "Running"
        toggle_text = "Resume Keep-Alive" if self._paused else "Pause Keep-Alive"

        return pystray.Menu(
            pystray.MenuItem(
                f"Status: {status_text}",
                None,
                enabled=False,
                default=True,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                toggle_text,
                self._on_toggle_pause,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Settings...",
                self._on_open_settings,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Exit",
                self._on_exit,
            ),
        )

    def _on_toggle_pause(self, _icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        engine = self._app.engine
        if engine.is_running:
            engine.pause()
            self._paused = True
            self.update_icon(False)
            self.update_tooltip("AudioKeep - Paused")
        elif engine.is_paused:
            engine.resume()
            self._paused = False
            self.update_icon(True)
            self.update_tooltip("AudioKeep - Running")
        self._rebuild_menu()

    def _on_open_settings(self, _icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        self._app.open_settings()

    def _on_exit(self, _icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        self._app.shutdown()
