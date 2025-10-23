"""
Async runtime entry for the Whisplay chatbot.
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import suppress
from pathlib import Path
from typing import Optional

from .config import ChatbotSettings, DATA_DIR, get_settings
from .core import ChatFlow
from .hardware.board import MockBoard
from .logging_utils import configure_logging
from .runtime import build_runtime

logger = logging.getLogger(__name__)


async def run_chatbot(
    *,
    simulate_override: Optional[bool] = None,
    log_level: Optional[str] = None,
    log_file: Optional[Path] = None,
) -> None:
    """
    Bootstraps the chatbot and starts the asynchronous chat flow.
    """

    settings = _load_settings(simulate_override=simulate_override)

    log_dir = getattr(settings, "log_dir", DATA_DIR / "logs")
    level = log_level or getattr(settings, "log_level", None)
    log_path = configure_logging(log_dir=log_dir, log_level=level, log_file=log_file)
    logger.info("Logging to %s", log_path)

    runtime = build_runtime(settings)
    if runtime.using_mock_board:
        logger.warning(
            "Mock Whisplay board active. Set WHISPLAY_ENABLE_SIMULATION=0 on hardware."
        )
    else:
        logger.info("Whisplay hardware board initialised successfully.")

    chat_flow = ChatFlow(runtime.components)
    loop = asyncio.get_running_loop()

    async def shutdown() -> None:
        logger.info("Shutting down chatbot...")
        await chat_flow.stop()
        with suppress(Exception):
            cleanup = getattr(runtime.board, "cleanup", None)
            if callable(cleanup):
                cleanup()
        for task in asyncio.all_tasks(loop):
            if task is asyncio.current_task(loop):
                continue
            task.cancel()

    for signal_name in ("SIGINT", "SIGTERM"):
        with suppress(AttributeError):
            loop.add_signal_handler(
                getattr(__import__("signal"), signal_name),
                lambda s=signal_name: asyncio.create_task(shutdown()),
            )

    logger.info("Startup complete; awaiting interactions (simulation=%s)", settings.enable_simulation)
    await chat_flow.run()


def _load_settings(*, simulate_override: Optional[bool]) -> ChatbotSettings:
    if simulate_override is not None:
        os.environ["WHISPLAY_ENABLE_SIMULATION"] = "1" if simulate_override else "0"
    get_settings.cache_clear()  # type: ignore[attr-defined]
    return get_settings()


def main() -> None:
    try:
        asyncio.run(run_chatbot())
    except KeyboardInterrupt:
        print("\nGoodbye from Whisplay! 👋")
