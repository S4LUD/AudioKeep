"""Build script for creating a standalone Windows executable with PyInstaller."""

import subprocess
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent
_ENTRY = _PROJECT_ROOT / "audiokeep" / "main.py"
_APP_NAME = "AudioKeep"
_PNG_ICON = _PROJECT_ROOT / "audio_keep_icon.png"


def build() -> None:
    icon_path = (_PROJECT_ROOT / "assets" / "icon.ico").resolve()
    entry_path = _ENTRY.resolve()
    png_path = _PNG_ICON.resolve()

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        _APP_NAME,
        "--hidden-import",
        "pystray._win32",
        "--hidden-import",
        "sounddevice",
        str(entry_path),
    ]

    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])

    if png_path.exists():
        cmd.extend(["--add-data", f"{png_path};."])

    print(f"Building {_APP_NAME}...")
    subprocess.run(cmd, check=True, cwd=_PROJECT_ROOT)
    print(f"Done. Executable: {(_PROJECT_ROOT / 'dist' / (_APP_NAME + '.exe')).resolve()}")


if __name__ == "__main__":
    build()
