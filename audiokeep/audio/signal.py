"""Noise generation for the keep-alive signal."""

import numpy as np

# Pre-computed default amplitude for -70 dB
_DEFAULT_AMPLITUDE = 10.0 ** (-70.0 / 20.0)


def generate_noise(frames: int, channels: int, amplitude: float = _DEFAULT_AMPLITUDE) -> np.ndarray:
    """Generate a buffer of low-amplitude white noise as float32.

    Parameters
    ----------
    frames : int
        Number of audio frames to generate.
    channels : int
        Number of output channels.
    amplitude : float
        Linear amplitude (derived from dB via ``10 ** (db / 20)``).

    Returns
    -------
    numpy.ndarray
        Shape ``(frames, channels)``, dtype ``float32``.
    """
    noise = np.random.uniform(-1.0, 1.0, size=(frames, channels)).astype(np.float32)
    noise *= amplitude
    return noise
