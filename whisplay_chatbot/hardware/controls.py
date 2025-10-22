"""
Button and input controls abstraction.
"""

from __future__ import annotations

import asyncio
import sys
from typing import Optional

from .board import DisplayBoard, MockBoard


class ControlManager:
    def __init__(self, board: DisplayBoard, simulate: bool = False):
        self.board = board
        self.simulate = simulate or isinstance(board, MockBoard)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._press_event = asyncio.Event()
        self._release_event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        self._loop = asyncio.get_running_loop()
        if self.simulate:
            self._task = asyncio.create_task(self._keyboard_listener())
        else:
            self.board.on_button_press(self._on_press)
            self.board.on_button_release(self._on_release)

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def wait_for_press(self) -> None:
        await self._press_event.wait()
        self._press_event.clear()

    async def wait_for_release(self) -> None:
        await self._release_event.wait()
        self._release_event.clear()

    def _on_press(self) -> None:
        if self._loop:
            self._loop.call_soon_threadsafe(self._press_event.set)

    def _on_release(self) -> None:
        if self._loop:
            self._loop.call_soon_threadsafe(self._release_event.set)

    async def _keyboard_listener(self) -> None:
        prompt = (
            "\n[Whisplay] Press Enter to simulate button press and Enter again to release.\n"
        )
        print(prompt, file=sys.stderr)
        while True:
            await asyncio.to_thread(sys.stdin.readline)
            if self._loop:
                self._loop.call_soon_threadsafe(self._press_event.set)
            await asyncio.to_thread(sys.stdin.readline)
            if self._loop:
                self._loop.call_soon_threadsafe(self._release_event.set)


import contextlib  # noqa: E402
