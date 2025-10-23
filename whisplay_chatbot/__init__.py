"""Whisplay Chatbot package."""

from __future__ import annotations


def main() -> None:
    """Convenience entry point that defers to the Typer CLI."""
    from .app import main as _main

    _main()


__all__ = ["main"]
