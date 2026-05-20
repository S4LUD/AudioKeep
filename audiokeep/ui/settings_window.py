"""Settings window using customtkinter."""

import logging
import sys
import threading
import tkinter as tk
from pathlib import Path
from typing import TYPE_CHECKING

import customtkinter as ctk

from audiokeep.audio.devices import list_output_devices
from audiokeep.config.models import MAX_LEVEL_DB, MIN_LEVEL_DB, AppSettings
from audiokeep.system.autostart import set_auto_start

if TYPE_CHECKING:
    from audiokeep.app import App

logger = logging.getLogger(__name__)

_PRESETS = {
    "Minimal (-80 dB)": -80.0,
    "Normal (-70 dB)": -70.0,
    "Strong (-60 dB)": -60.0,
}


class SettingsWindow:
    """Settings dialog for AudioKeep."""

    def __init__(self, app: "App") -> None:
        self._app = app
        self._window: ctk.CTkToplevel | None = None
        self._device_var: ctk.StringVar | None = None
        self._level_var: ctk.DoubleVar | None = None
        self._level_label: ctk.CTkLabel | None = None
        self._auto_start_var: ctk.BooleanVar | None = None
        self._start_min_var: ctk.BooleanVar | None = None
        self._device_map: dict[str, int] = {}
        self._apply_btn: ctk.CTkButton | None = None
        self._test_btn: ctk.CTkButton | None = None
        self._status_label: ctk.CTkLabel | None = None

    def show(self) -> None:
        """Show the settings window (create if needed). Must be called on the main thread."""
        if self._window is not None and self._window.winfo_exists():
            self._window.focus_force()
            return

        self._window = ctk.CTkToplevel()
        self._window.title("AudioKeep Settings")
        self._window.resizable(False, False)
        self._window.attributes("-topmost", True)

        # Set window icon
        icon_path = self._find_icon()
        if icon_path:
            try:
                from PIL import ImageTk
                img = ImageTk.PhotoImage(file=icon_path)
                self._window.iconphoto(True, img)
                self._icon_ref = img  # prevent garbage collection
            except Exception:
                pass

        self._window.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._load_current_values()

        # Fixed size and center on screen
        w, h = 440, 340
        sx = self._window.winfo_screenwidth()
        sy = self._window.winfo_screenheight()
        x = (sx - w) // 2
        y = (sy - h) // 2
        self._window.geometry(f"{w}x{h}+{x}+{y}")

        self._window.after(100, lambda: self._window.focus_force())

    def _build_ui(self) -> None:
        assert self._window is not None
        win = self._window
        settings = self._app.settings
        px = 12  # horizontal padding

        # --- Output Device ---
        ctk.CTkLabel(win, text="Output Device", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", padx=px, pady=(10, 2)
        )
        devices = list_output_devices()
        device_names = [d.name for d in devices]
        self._device_map = {d.name: d.index for d in devices}

        self._device_var = ctk.StringVar(value=settings.output_device_name or "")
        ctk.CTkComboBox(
            win,
            variable=self._device_var,
            values=device_names,
            state="readonly",
        ).pack(fill="x", padx=px, pady=(0, 6))

        # --- Keep-alive Level ---
        ctk.CTkLabel(win, text="Keep-Alive Level (dB)", font=ctk.CTkFont(weight="bold")).pack(
            anchor="w", padx=px, pady=(0, 2)
        )
        self._level_var = ctk.DoubleVar(value=settings.keep_alive_level_db)

        level_frame = ctk.CTkFrame(win, fg_color="transparent")
        level_frame.pack(fill="x", padx=px, pady=(0, 0))

        self._level_label = ctk.CTkLabel(level_frame, text=f"{settings.keep_alive_level_db:.0f} dB")
        self._level_label.pack(side="right")

        self._level_slider = ctk.CTkSlider(
            level_frame,
            from_=MIN_LEVEL_DB,
            to=MAX_LEVEL_DB,
            variable=self._level_var,
            command=self._on_level_change,
        )
        self._level_slider.pack(side="left", fill="x", expand=True)

        range_frame = ctk.CTkFrame(win, fg_color="transparent")
        range_frame.pack(fill="x", padx=px, pady=(0, 6))
        ctk.CTkLabel(range_frame, text="-90 dB", text_color="gray", font=("", 11)).pack(side="left")
        ctk.CTkLabel(range_frame, text="-50 dB", text_color="gray", font=("", 11)).pack(side="right")

        # --- Presets ---
        preset_frame = ctk.CTkFrame(win, fg_color="transparent")
        preset_frame.pack(fill="x", padx=px, pady=(0, 8))
        for label, db_val in _PRESETS.items():
            ctk.CTkButton(
                preset_frame,
                text=label,
                width=120,
                height=26,
                command=lambda v=db_val: self._apply_preset(v),
            ).pack(side="left", padx=(0, 4))

        # --- Checkboxes ---
        self._auto_start_var = ctk.BooleanVar(value=settings.auto_start)
        ctk.CTkCheckBox(
            win,
            text="Auto-start with Windows",
            variable=self._auto_start_var,
        ).pack(anchor="w", padx=px, pady=1)

        self._start_min_var = ctk.BooleanVar(value=settings.start_minimized)
        ctk.CTkCheckBox(
            win,
            text="Start minimized to tray",
            variable=self._start_min_var,
        ).pack(anchor="w", padx=px, pady=(1, 8))

        # --- Buttons ---
        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(fill="x", padx=px, pady=(4, 2))

        ctk.CTkButton(
            btn_frame, text="Reset", width=80, height=28, fg_color="gray",
            command=self._on_reset,
        ).pack(side="left")

        self._test_btn = ctk.CTkButton(
            btn_frame, text="Test", width=60, height=28,
            command=self._on_test,
        )
        self._test_btn.pack(side="left", padx=(6, 0))

        self._apply_btn = ctk.CTkButton(
            btn_frame, text="Apply", width=80, height=28,
            command=self._on_apply,
        )
        self._apply_btn.pack(side="right")

        # --- Status label (hidden by default) ---
        self._status_label = ctk.CTkLabel(
            win, text="", text_color="#4CAF50", font=("", 12),
        )
        self._status_label.pack(anchor="e", padx=px, pady=(0, 4))

    @staticmethod
    def _find_icon() -> str | None:
        if getattr(sys, "frozen", False):
            base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        else:
            base = Path(__file__).resolve().parent.parent.parent
        for name in ("audio_keep_icon.png", "assets/audio_keep_icon.png"):
            p = base / name
            if p.exists():
                return str(p)
        return None

    def _load_current_values(self) -> None:
        settings = self._app.settings
        if self._device_var:
            current = settings.output_device_name or ""
            if current in self._device_map:
                self._device_var.set(current)
            elif self._device_combo.cget("values"):
                self._device_var.set(self._device_combo.cget("values")[0])

    def _on_level_change(self, value: float) -> None:
        if self._level_label:
            self._level_label.configure(text=f"{value:.0f} dB")

    def _apply_preset(self, db_val: float) -> None:
        if self._level_var:
            self._level_var.set(db_val)
        if self._level_label:
            self._level_label.configure(text=f"{db_val:.0f} dB")

    def _on_apply(self) -> None:
        if not self._device_var or not self._level_var:
            return

        device_name = self._device_var.get() or None
        level_db = round(self._level_var.get(), 1)
        auto_start = self._auto_start_var.get() if self._auto_start_var else False
        start_min = self._start_min_var.get() if self._start_min_var else True

        self._app.store.update(
            output_device_name=device_name,
            keep_alive_level_db=level_db,
            auto_start=auto_start,
            start_minimized=start_min,
        )
        set_auto_start(auto_start)

        # Apply to running engine
        self._app.engine.update_settings(self._app.store.settings)
        self._app.engine.stop()
        self._app.engine.start()

        logger.info("Settings applied: device=%s, level=%.1f dB", device_name, level_db)
        self._show_status("Applied!")

    def _on_test(self) -> None:
        """Briefly play noise for 1 second to verify audio is working."""
        import sounddevice as sd
        from audiokeep.audio.signal import generate_noise

        if self._test_btn:
            self._test_btn.configure(state="disabled", text="...")
        self._show_status("Playing 1s test tone...")

        level_db = self._level_var.get() if self._level_var else -70.0
        amp = 10.0 ** (level_db / 20.0)
        sr = self._app.settings.sample_rate
        frames = sr  # 1 second

        def _play() -> None:
            try:
                noise = generate_noise(frames, 2, amp)
                sd.play(noise, samplerate=sr, blocking=True)
            except Exception as exc:
                logger.error("Test playback failed: %s", exc)
            finally:
                if self._window and self._test_btn:
                    self._window.after(0, lambda: self._test_btn.configure(state="normal", text="Test"))
                    self._window.after(0, lambda: self._show_status("Test complete"))

        threading.Thread(target=_play, daemon=True).start()

    def _on_reset(self) -> None:
        defaults = AppSettings()
        if self._level_var:
            self._level_var.set(defaults.keep_alive_level_db)
        if self._level_label:
            self._level_label.configure(text=f"{defaults.keep_alive_level_db:.0f} dB")
        if self._auto_start_var:
            self._auto_start_var.set(defaults.auto_start)
        if self._start_min_var:
            self._start_min_var.set(defaults.start_minimized)

    def _show_status(self, text: str) -> None:
        if self._status_label:
            self._status_label.configure(text=text)
            self._window.after(2000, lambda: self._status_label.configure(text=""))

    def _on_close(self) -> None:
        if self._window:
            self._window.destroy()
            self._window = None
