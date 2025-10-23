"""Whisplay Chatbot package."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

__all__ = ["main", "get_app"]


def main() -> None:
    """Entrypoint used by `python -m whisplay_chatbot`."""
    from .main import main as _main

    _main()


def get_app() -> Any:
    """
    Return the Typer application without importing it at module load time.

    Avoids circular import warnings when running `python -m whisplay_chatbot.main`.
    """

    from .main import app

    return app
