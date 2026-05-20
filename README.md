# AudioKeep

A lightweight Windows system tray utility that prevents Bluetooth speakers and headsets from sleeping, cutting off quiet audio, or clipping the first sound after silence.

## Why does Bluetooth audio cut off on PC?

Most Bluetooth audio devices use power-saving profiles that put the device into a low-power sleep mode after a few seconds of silence. When new audio starts playing, the device needs to wake up and re-establish the A2DP audio stream. This causes:

- **Clipped beginnings**: The first 0.5-2 seconds of a song, notification, or voice call are cut off.
- **Audio dropouts**: Brief pauses in music or podcasts cause the device to sleep and miss content.
- **Connection delays**: The Bluetooth stack may need to re-negotiate codecs, adding latency.

AudioKeep fixes this by continuously outputting an ultra-low-volume noise floor that keeps the Bluetooth audio pipeline active. The noise is randomized (not a tone) and set well below the audible threshold during normal use.

## Installation

Download `AudioKeep.exe` from the [Releases](https://github.com/S4LUD/AudioKeep/releases) page and run it. No installation or dependencies required.

## Recommended settings

| Preset  | Level  | When to use                                                |
|---------|--------|------------------------------------------------------------|
| Minimal | -80 dB | Devices that sleep aggressively even with quiet signals.    |
| Normal  | -70 dB | Most Bluetooth devices. Best balance of safety and reliability. |
| Strong  | -60 dB | Devices that ignore very quiet signals. Still inaudible during normal use. |

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
- **Persistent settings**: All settings saved automatically.
- **Low CPU usage**: Negligible CPU impact.
- **Single-instance protection**: Prevents multiple copies from running.

## Troubleshooting

### AudioKeep doesn't seem to keep my device awake

1. Open Settings and try the **Strong** preset (-60 dB).
2. Verify the correct output device is selected in the dropdown.
3. Some devices require a higher signal level — try -50 dB.
4. Check that AudioKeep shows "Running" in the tray menu.

### I can hear the noise

1. Lower the keep-alive level toward -80 or -90 dB.
2. On very efficient headphones, -90 dB may still be perceptible. Use the lowest level that still prevents sleep.

### How do I stop AudioKeep?

Right-click the tray icon and select **Exit**. To prevent it from starting with Windows, uncheck "Auto-start with Windows" in Settings.

## Safety notes

- AudioKeep **never** generates loud output. All output is clamped between -90 dB and -50 dB.
- AudioKeep **does not** modify system audio drivers, codecs, or Bluetooth settings.
- AudioKeep **does not** require administrator privileges.
- AudioKeep **does not** collect telemetry or connect to the internet.
- AudioKeep **does not** interfere with other audio applications.
- The noise output is **white noise** (randomized), not a tone.

## License

MIT
