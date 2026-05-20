"""Output device discovery and selection."""

import logging
from dataclasses import dataclass

import sounddevice as sd

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OutputDevice:
    """Represents an audio output device."""
    index: int
    name: str
    channels: int
    sample_rate: float
    hostapi: str


def list_output_devices() -> list[OutputDevice]:
    """Return unique available output devices, deduplicated by name.

    Keeps the first occurrence per device name (sounddevice lists higher-priority
    APIs first, so this favors WASAPI > DirectSound > MME).
    Filters out virtual mapper entries like 'Microsoft Sound Mapper'.
    """
    devices: list[OutputDevice] = []
    seen_names: set[str] = set()
    try:
        all_devices = sd.query_devices()
        hostapis = sd.query_hostapis()
        for i, dev in enumerate(all_devices):
            if dev["max_output_channels"] <= 0:
                continue
            name = dev["name"]
            # Skip virtual mappers
            if "Sound Mapper" in name or "Primary Sound" in name:
                continue
            if name in seen_names:
                continue
            seen_names.add(name)
            hostapi_name = hostapis[dev["hostapi"]]["name"] if dev["hostapi"] < len(hostapis) else "Unknown"
            devices.append(
                OutputDevice(
                    index=i,
                    name=name,
                    channels=dev["max_output_channels"],
                    sample_rate=dev["default_samplerate"],
                    hostapi=hostapi_name,
                )
            )
    except Exception as exc:
        logger.error("Failed to enumerate output devices: %s", exc)
    return devices


def find_device_by_name(name: str) -> OutputDevice | None:
    """Find an output device by exact name match."""
    for dev in list_output_devices():
        if dev.name == name:
            return dev
    return None


def get_default_output_device() -> OutputDevice | None:
    """Return the system default output device (the real device, not a mapper)."""
    try:
        all_devices = sd.query_devices()
        hostapis = sd.query_hostapis()

        # sd.default.device is (input_index, output_index)
        dev_index = sd.default.device[1]
        if dev_index < 0 or dev_index >= len(all_devices):
            # Fallback: query_devices(kind="output") returns the mapper
            default = sd.query_devices(kind="output")
            for i, d in enumerate(all_devices):
                if d["name"] == default["name"] and d["max_output_channels"] > 0:
                    dev_index = i
                    break
            else:
                return None

        dev = all_devices[dev_index]
        if dev["max_output_channels"] <= 0:
            return None

        hostapi_name = hostapis[dev["hostapi"]]["name"] if dev["hostapi"] < len(hostapis) else "Unknown"
        return OutputDevice(
            index=dev_index,
            name=dev["name"],
            channels=dev["max_output_channels"],
            sample_rate=dev["default_samplerate"],
            hostapi=hostapi_name,
        )
    except Exception as exc:
        logger.error("Failed to query default output device: %s", exc)
        return None


def resolve_output_device(preferred_name: str | None) -> OutputDevice | None:
    """Resolve the best available output device.

    Tries the preferred name first, then falls back to system default.
    """
    if preferred_name:
        dev = find_device_by_name(preferred_name)
        if dev:
            logger.info("Using preferred device: %s", dev.name)
            return dev
        logger.warning("Preferred device '%s' not found; falling back to default.", preferred_name)
    dev = get_default_output_device()
    if dev:
        logger.info("Using default device: %s", dev.name)
    else:
        logger.error("No output device available.")
    return dev
