"""Settings data model with validation."""

from pydantic import BaseModel, Field, field_validator

# Constants
DEFAULT_LEVEL_DB = -70.0
MIN_LEVEL_DB = -90.0
MAX_LEVEL_DB = -50.0
DEFAULT_SAMPLE_RATE = 48000
DEFAULT_CHANNELS = 2


class AppSettings(BaseModel):
    """Validated application settings."""

    output_device_name: str | None = Field(
        default=None,
        description="Name of the selected output device. None uses system default.",
    )
    keep_alive_level_db: float = Field(
        default=DEFAULT_LEVEL_DB,
        description="Keep-alive noise level in dB.",
    )
    auto_start: bool = Field(
        default=False,
        description="Launch AudioKeep when Windows starts.",
    )
    start_minimized: bool = Field(
        default=True,
        description="Start minimized to system tray.",
    )
    sample_rate: int = Field(
        default=DEFAULT_SAMPLE_RATE,
        description="Audio output sample rate in Hz.",
    )
    channels: int = Field(
        default=DEFAULT_CHANNELS,
        description="Number of audio output channels.",
    )

    @field_validator("keep_alive_level_db")
    @classmethod
    def clamp_level(cls, v: float) -> float:
        return max(MIN_LEVEL_DB, min(MAX_LEVEL_DB, v))

    def db_to_amplitude(self) -> float:
        """Convert keep-alive level from dB to linear amplitude."""
        return 10.0 ** (self.keep_alive_level_db / 20.0)
