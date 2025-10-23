"""
Centralised logging configuration for the Whisplay chatbot.
"""

from __future__ import annotations

import logging
from logging import Handler
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Iterable, Optional

DEFAULT_LOG_FORMAT = "[%(asctime)s] %(levelname)s %(name)s: %(message)s"


def _resolve_level(level_name: Optional[str]) -> int:
    if not level_name:
        return logging.INFO
    try:
        return getattr(logging, level_name.upper())
    except AttributeError as exc:  # pragma: no cover - defensive branch
        raise ValueError(f"Unknown log level '{level_name}'") from exc


def configure_logging(
    *,
    log_dir: Path,
    log_level: Optional[str] = None,
    log_file: Optional[Path] = None,
    extra_handlers: Iterable[Handler] | None = None,
) -> Path:
    """
    Configure the logging subsystem.

    Returns the path to the file handler that was created.
    """

    log_dir.mkdir(parents=True, exist_ok=True)
    file_path = log_file or (log_dir / "whisplay.log")

    stream_handler = logging.StreamHandler()
    file_handler = RotatingFileHandler(file_path, maxBytes=2_000_000, backupCount=3, encoding="utf-8")

    handlers: list[Handler] = [stream_handler, file_handler]
    if extra_handlers:
        handlers.extend(extra_handlers)

    logging.basicConfig(
        level=_resolve_level(log_level),
        format=DEFAULT_LOG_FORMAT,
        handlers=handlers,
        force=True,
    )

    logging.getLogger(__name__).debug("Logging configured (file=%s)", file_path)
    return Path(file_path)
