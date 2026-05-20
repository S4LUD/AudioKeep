"""Rotating-file logging configuration."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_FORMAT = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
_LOG_MAX_BYTES = 512 * 1024  # 512 KB per file
_LOG_BACKUP_COUNT = 3


def setup_logging(log_dir: Path, level: int = logging.INFO) -> None:
    """Configure root logger with a rotating file handler and a console handler."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "audiokeep.log"

    root = logging.getLogger()
    root.setLevel(level)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=_LOG_MAX_BYTES,
        backupCount=_LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root.addHandler(console_handler)
