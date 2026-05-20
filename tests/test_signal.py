"""Tests for the noise signal generator."""

import numpy as np
import pytest

from audiokeep.audio.signal import generate_noise


class TestGenerateNoise:
    def test_shape(self):
        noise = generate_noise(1024, 2, amplitude=0.001)
        assert noise.shape == (1024, 2)

    def test_dtype(self):
        noise = generate_noise(512, 2, amplitude=0.001)
        assert noise.dtype == np.float32

    def test_amplitude_bounded(self):
        amp = 10.0 ** (-60.0 / 20.0)  # -60 dB
        noise = generate_noise(48000, 2, amplitude=amp)
        assert np.max(np.abs(noise)) <= amp + 1e-6

    def test_not_all_zeros(self):
        noise = generate_noise(1024, 2, amplitude=1e-5)
        assert np.any(noise != 0)

    def test_stereo_independence(self):
        noise = generate_noise(10000, 2, amplitude=0.01)
        # Channels should not be identical
        assert not np.array_equal(noise[:, 0], noise[:, 1])

    def test_zero_amplitude(self):
        noise = generate_noise(512, 2, amplitude=0.0)
        assert np.all(noise == 0)

    def test_single_channel(self):
        noise = generate_noise(512, 1, amplitude=0.001)
        assert noise.shape == (512, 1)
