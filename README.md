# AudioKeep

A lightweight Windows system tray utility that prevents Bluetooth speakers and headsets from sleeping, cutting off quiet audio, or clipping the first sound after silence.

## Why does Bluetooth audio cut off on PC?

Most Bluetooth audio devices use power-saving profiles that put the device into a low-power sleep mode after a few seconds of silence (or very quiet audio). When new audio starts playing, the device needs to wake up and re-establish the A2DP audio stream. This causes:

- **Clipped beginnings**: The first 0.5-2 seconds of a song, notification, or voice call are cut off.
- **Audio dropouts**: Brief pauses in music or podcasts cause the device to sleep and miss content.
- **Connection delays**: The Bluetooth stack may need to re-negotiate codecs, adding latency.

AudioKeep solves this by continuously outputting an ultra-low-volume noise floor that keeps the Bluetooth audio pipeline active. The noise is randomized (not a tone) and set well below the audible threshold during normal use.

## Installation

### From source

```bash
pip install -e ".[dev]"
```

### Run

```bash
python -m audiokeep
```

Or directly:

```bash
python audiokeep/main.py
```

## Building a standalone executable

```bash
pip install pyinstaller
python build.py
```

This produces `dist/AudioKeep.exe` — a single-file Windows executable that does not require Python to be installed.

## Recommended dB settings

| Preset    | Level    | When to use                                              |
|-----------|----------|----------------------------------------------------------|
| Minimal   | -80 dB   | Devices that sleep aggressively even with quiet signals.  |
| Normal    | -70 dB   | Most Bluetooth devices. Best balance of safety and reliability. |
| Strong    | -60 dB   | Devices that ignore very quiet signals. Still inaudible during normal use. |

The allowed range is **-90 dB** to **-50 dB**. The default is **-70 dB**.

### How loud is this?

- **-70 dB** is roughly the level of a pin drop at 1 meter. It is inaudible in any normal environment.
- **-50 dB** is roughly the level of a quiet room at night. Still very quiet, but occasionally perceptible if you listen carefully in a silent room with headphones.
- AudioKeep never plays tones — only randomized noise, which is far less noticeable than any pure tone.

## Features

- **System tray app**: Runs in the background with a small icon. Right-click for the menu.
- **Adjustable level**: Slider from -90 dB to -50 dB with presets.
- **Output device selection**: Choose any audio output device. Falls back to the system default if the selected device is disconnected.
- **Auto-start with Windows**: Optional. Uses the HKCU registry key (no admin required).
- **Start minimized**: Launch directly to the system tray.
- **Pause/resume**: Temporarily stop the keep-alive without closing the app.
- **Persistent settings**: All settings saved automatically in `%APPDATA%/audiokeep/settings.json`.
- **Low CPU usage**: The noise generator runs in the audio callback thread — negligible CPU impact.
- **Clean shutdown**: Gracefully stops the audio stream and releases resources.

## Architecture

```
audiokeep/
  __init__.py          # Package metadata
  main.py              # Entry point
  app.py               # Application controller (wires everything together)
  audio/
    engine.py          # Audio stream lifecycle management
    devices.py         # Output device discovery and selection
    signal.py          # Noise generation (numpy)
  config/
    models.py          # Pydantic settings model with validation
    store.py           # JSON-backed settings persistence
  ui/
    tray.py            # System tray icon and menu (pystray)
    settings_window.py # Settings dialog (customtkinter)
  system/
    autostart.py       # Windows registry auto-start
    logging_setup.py   # Rotating log file configuration
    paths.py           # Platform-specific directory paths
  utils/
    thread_safe.py     # Thread-safe state machine

tests/
  test_config.py       # Config model and store tests
  test_signal.py       # Noise generation tests
  test_autostart.py    # Auto-start registry tests (mocked)
```

### Design principles

- **Separation of concerns**: Audio engine, UI, config, and system integration are isolated modules.
- **Thread safety**: The `StateManager` provides a lock-based state machine. The audio callback uses a lock only to read the current amplitude (no blocking).
- **Defensive validation**: Pydantic models validate all settings. Corrupt configs are backed up and replaced with defaults.
- **No global mutable state**: All state lives in well-defined objects (`App`, `AudioEngine`, `SettingsStore`).
- **Graceful degradation**: Device disconnect, sample rate mismatch, and permission errors are handled without crashing.

## Error handling strategy

| Scenario | Behavior |
|---|---|
| Selected device disconnected | Falls back to system default device |
| No output devices available | Logs error, tray icon shows paused state |
| Corrupt config file | Backs up corrupt file, loads defaults |
| Sample rate mismatch | Uses device's native sample rate |
| PortAudio error | Logs error, stops stream, prevents crash |
| Permission error | Logs error, shows in tray status |

## Troubleshooting

### AudioKeep doesn't seem to keep my device awake

1. Open Settings and try the **Strong** preset (-60 dB).
2. Verify the correct output device is selected in the dropdown.
3. Some devices require a higher signal level — try -50 dB.
4. Check that AudioKeep shows "Running" in the tray menu.

### I can hear the noise

1. Lower the keep-alive level toward -80 or -90 dB.
2. The noise is white noise, which is less noticeable than tones. If you can hear it in a silent room, reduce the level until it's inaudible.
3. On very efficient headphones/IEMs, -90 dB may still be perceptible. This is expected — use the lowest level that still prevents sleep.

### AudioKeep won't start

1. Check that you have a working audio output device.
2. Check the log file at `%LOCALAPPDATA%/audiokeep/audiokeep.log`.
3. Ensure `sounddevice` and its PortAudio backend are installed correctly.

### How do I stop AudioKeep?

Right-click the tray icon and select **Exit**. To prevent it from starting with Windows, uncheck "Auto-start with Windows" in Settings.

## Safety notes

- AudioKeep **never** generates loud output. All output is clamped between -90 dB and -50 dB.
- AudioKeep **does not** modify system audio drivers, codecs, or Bluetooth settings.
- AudioKeep **does not** require administrator privileges.
- AudioKeep **does not** collect telemetry or connect to the internet.
- AudioKeep **does not** interfere with other audio applications — it outputs on a separate audio stream.
- The noise output is **white noise** (randomized), not a tone. It does not interfere with music or voice content.

## License

MIT
