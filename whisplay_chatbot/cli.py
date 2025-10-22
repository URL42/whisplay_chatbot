"""
Typer CLI for Whisplay chatbot.
"""

from __future__ import annotations

import asyncio

import typer

from .app import run_chatbot

app = typer.Typer(add_completion=False)


@app.command()
def run() -> None:
    """Launch the Whisplay chatbot."""
    asyncio.run(run_chatbot())


@app.command()
def simulate() -> None:
    """Run the chatbot in simulation mode (no Pi hardware required)."""
    import os

    os.environ["WHISPLAY_ENABLE_SIMULATION"] = "1"
    asyncio.run(run_chatbot())


if __name__ == "__main__":
    app()
