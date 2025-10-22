"""
LED animation helper.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from dataclasses import dataclass

from .board import DisplayBoard

logger = logging.getLogger(__name__)


@dataclass
class LedState:
    color: tuple[int, int, int]
    mode: str = "solid"  # solid | pulse | breathing | sparkle


class LedAnimator:
    def __init__(self, board: DisplayBoard):
        self.board = board
        self.state = LedState((0, 0, 0), mode="solid")
        self._task: asyncio.Task | None = None
        self._queue: asyncio.Queue[LedState] = asyncio.Queue()

    async def start(self) -> None:
        if self._task:
            return
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def set_state(self, color: tuple[int, int, int], mode: str = "solid") -> None:
        await self._queue.put(LedState(color=color, mode=mode))

    async def _run(self) -> None:
        while True:
            try:
                try:
                    self.state = self._queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass

                mode = self.state.mode
                color = self.state.color

                if mode == "solid":
                    self.board.set_rgb(*color)
                    await asyncio.sleep(0.2)
                elif mode == "pulse":
                    await self._pulse(color)
                elif mode == "breathing":
                    await self._breathing(color)
                elif mode == "sparkle":
                    await self._sparkle(color)
                else:
                    logger.debug("Unknown LED mode '%s'", mode)
                    await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("LED animator error")
                await asyncio.sleep(0.5)

    async def _pulse(self, color: tuple[int, int, int]) -> None:
        for scale in list(range(20, 101, 12)) + list(range(100, 19, -12)):
            scaled = tuple(int(c * scale / 100) for c in color)
            self.board.set_rgb(*scaled)
            await asyncio.sleep(0.05)

    async def _breathing(self, color: tuple[int, int, int]) -> None:
        for scale in list(range(10, 101, 5)) + list(range(100, 9, -5)):
            scaled = tuple(int(c * scale / 100) for c in color)
            self.board.set_rgb_fade(*scaled, duration_ms=120)
            await asyncio.sleep(0.08)

    async def _sparkle(self, color: tuple[int, int, int]) -> None:
        import random

        for _ in range(12):
            sparkle_color = tuple(min(255, int(c * random.uniform(0.6, 1.2))) for c in color)
            self.board.set_rgb(*sparkle_color)
            await asyncio.sleep(0.07)
        self.board.set_rgb(*color)
