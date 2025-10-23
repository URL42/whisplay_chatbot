"""
Typer CLI entry point for the Whisplay chatbot.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Optional

import typer

from .app import run_chatbot
from .config import get_settings

app = typer.Typer(add_completion=False, rich_markup_mode="markdown")


def _prepare_environment(
    *,
    simulate: Optional[bool],
    log_level: Optional[str],
) -> None:
    if simulate is not None:
        os.environ["WHISPLAY_ENABLE_SIMULATION"] = "1" if simulate else "0"
    if log_level is not None:
        os.environ["WHISPLAY_LOG_LEVEL"] = log_level
    get_settings.cache_clear()  # type: ignore[attr-defined]


def _run_async(
    *,
    simulate: Optional[bool] = None,
    log_level: Optional[str] = None,
    log_file: Optional[Path] = None,
) -> None:
    _prepare_environment(simulate=simulate, log_level=log_level)
    asyncio.run(
        run_chatbot(
            simulate_override=simulate,
            log_level=log_level,
            log_file=log_file,
        )
    )


@app.command()
def run(
    simulate: bool = typer.Option(False, help="Force keyboard simulation mode."),
    log_level: Optional[str] = typer.Option(
        None,
        "--log-level",
        "-l",
        help="Override log level (e.g. DEBUG, INFO, WARNING).",
    ),
    log_file: Optional[Path] = typer.Option(
        None,
        "--log-file",
        help="Write logs to a custom file path (default: data/logs/whisplay.log).",
    ),
) -> None:
    """
    Launch the Whisplay chatbot. Use `--simulate` to run without Pi hardware.
    """

    simulate_override = True if simulate else None
    _run_async(simulate=simulate_override, log_level=log_level, log_file=log_file)


@app.command()
def simulate(
    log_level: Optional[str] = typer.Option(
        None,
        "--log-level",
        "-l",
        help="Override log level (e.g. DEBUG, INFO, WARNING).",
    ),
    log_file: Optional[Path] = typer.Option(
        None,
        "--log-file",
        help="Write logs to a custom file path (default: data/logs/whisplay.log).",
    ),
) -> None:
    """
    Convenience shortcut for running the chatbot in simulation mode.
    """

    _run_async(simulate=True, log_level=log_level, log_file=log_file)


def main() -> None:
    app()
