"""Audio engine: manages the keep-alive output stream."""

import logging
import threading
from typing import Callable

import numpy as np
import sounddevice as sd

from audiokeep.config.models import AppSettings
from audiokeep.utils.thread_safe import RunState, StateManager

from .devices import OutputDevice, resolve_output_device
from .signal import generate_noise

logger = logging.getLogger(__name__)

# Minimum frames per buffer for stable callback timing
_MIN_BLOCK_SIZE = 256
_DEFAULT_BLOCK_SIZE = 1024


class AudioEngine:
    """Manages the keep-alive audio stream lifecycle.

    Thread-safe: start(), pause(), resume(), stop() may be called from any thread.
    """

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._state = StateManager()
        self._stream: sd.OutputStream | None = None
        self._device: OutputDevice | None = None
        self._lock = threading.Lock()
        self._amplitude = settings.db_to_amplitude()
        self._sample_rate = settings.sample_rate
        self._channels = settings.channels
        self._error_callback: Callable[[str], None] | None = None

    @property
    def state(self) -> RunState:
        return self._state.state

    @property
    def device(self) -> OutputDevice | None:
        return self._device

    @property
    def is_running(self) -> bool:
        return self._state.is_active

    @property
    def is_paused(self) -> bool:
        return self._state.is_paused

    def set_error_callback(self, callback: Callable[[str], None] | None) -> None:
        """Register a callback for fatal stream errors."""
        self._error_callback = callback

    def update_settings(self, settings: AppSettings) -> None:
        """Apply new settings. Takes effect on the next audio callback."""
        with self._lock:
            self._settings = settings
            self._amplitude = settings.db_to_amplitude()
            self._sample_rate = settings.sample_rate
            self._channels = settings.channels

    def start(self) -> bool:
        """Start (or resume) the keep-alive stream."""
        if self._state.is_active:
            logger.debug("Engine already active.")
            return True

        if self._state.is_paused:
            return self.resume()

        if not self._state.transition(RunState.STOPPED, RunState.STARTING):
            logger.warning("Cannot start: state is %s", self._state.state)
            return False

        try:
            self._device = resolve_output_device(self._settings.output_device_name)
            if self._device is None:
                logger.error("No output device available.")
                self._state.transition(RunState.STARTING, RunState.STOPPED)
                return False

            effective_rate = int(self._device.sample_rate)
            if effective_rate != self._sample_rate:
                logger.info(
                    "Sample rate mismatch: requested %d, device %d. Using device rate.",
                    self._sample_rate,
                    effective_rate,
                )
                self._sample_rate = effective_rate

            self._stream = sd.OutputStream(
                samplerate=self._sample_rate,
                blocksize=_DEFAULT_BLOCK_SIZE,
                device=self._device.index,
                channels=self._channels,
                dtype="float32",
                callback=self._audio_callback,
                finished_callback=self._on_stream_finished,
            )
            self._stream.start()
            self._state.transition(RunState.STARTING, RunState.RUNNING)
            logger.info(
                "Audio engine started: device='%s', rate=%d, ch=%d, level=%.1f dB",
                self._device.name,
                self._sample_rate,
                self._channels,
                self._settings.keep_alive_level_db,
            )
            return True

        except sd.PortAudioError as exc:
            logger.error("PortAudio error starting stream: %s", exc)
            self._cleanup_stream()
            self._state.transition(RunState.STARTING, RunState.STOPPED)
            return False
        except Exception as exc:
            logger.error("Unexpected error starting engine: %s", exc)
            self._cleanup_stream()
            self._state.transition(RunState.STARTING, RunState.STOPPED)
            return False

    def pause(self) -> bool:
        """Pause the keep-alive stream without fully stopping it."""
        if not self._state.transition(RunState.RUNNING, RunState.PAUSING):
            return False
        self._cleanup_stream()
        self._state.transition(RunState.PAUSING, RunState.PAUSED)
        logger.info("Audio engine paused.")
        return True

    def resume(self) -> bool:
        """Resume from paused state."""
        if not self._state.transition(RunState.PAUSED, RunState.STARTING):
            return False
        try:
            self._device = resolve_output_device(self._settings.output_device_name)
            if self._device is None:
                logger.error("No output device for resume.")
                self._state.transition(RunState.STARTING, RunState.STOPPED)
                return False

            self._stream = sd.OutputStream(
                samplerate=self._sample_rate,
                blocksize=_DEFAULT_BLOCK_SIZE,
                device=self._device.index,
                channels=self._channels,
                dtype="float32",
                callback=self._audio_callback,
                finished_callback=self._on_stream_finished,
            )
            self._stream.start()
            self._state.transition(RunState.STARTING, RunState.RUNNING)
            logger.info("Audio engine resumed.")
            return True
        except Exception as exc:
            logger.error("Failed to resume: %s", exc)
            self._cleanup_stream()
            self._state.transition(RunState.STARTING, RunState.STOPPED)
            return False

    def stop(self) -> bool:
        """Stop the audio engine and release resources."""
        if not self._state.transition(RunState.RUNNING, RunState.STOPPING):
            if not self._state.transition(RunState.PAUSED, RunState.STOPPING):
                return False
        self._cleanup_stream()
        self._state.transition(RunState.STOPPING, RunState.STOPPED)
        logger.info("Audio engine stopped.")
        return True

    def _audio_callback(
        self,
        outdata: np.ndarray,
        frames: int,
        time_info: object,
        status: sd.CallbackFlags,
    ) -> None:
        """Sounddevice audio callback — must be lightweight and non-blocking."""
        if status:
            logger.debug("Audio callback status: %s", status)
        with self._lock:
            amp = self._amplitude
            ch = self._channels
        outdata[:] = generate_noise(frames, ch, amp)

    def _on_stream_finished(self) -> None:
        """Called by sounddevice when the stream closes."""
        logger.debug("Stream finished callback invoked.")
        with self._lock:
            if self._stream is not None:
                self._stream = None

    def _cleanup_stream(self) -> None:
        """Close and release the current stream safely."""
        with self._lock:
            stream = self._stream
            self._stream = None
        if stream is not None:
            try:
                if not stream.closed:
                    stream.stop()
                    stream.close()
            except Exception as exc:
                logger.debug("Error closing stream: %s", exc)

    def _handle_fatal_error(self, message: str) -> None:
        """Handle a fatal stream error: clean up and notify."""
        logger.error("Fatal audio error: %s", message)
        self._cleanup_stream()
        self._state.transition(RunState.RUNNING, RunState.STOPPED)
        if self._error_callback:
            try:
                self._error_callback(message)
            except Exception:
                pass
