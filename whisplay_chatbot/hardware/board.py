"""
Low-level board access for the PiSugar Whisplay HAT.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional, Protocol

logger = logging.getLogger(__name__)


class DisplayBoard(Protocol):
    LCD_WIDTH: int
    LCD_HEIGHT: int
    CornerHeight: int

    def draw_image(self, x: int, y: int, width: int, height: int, pixel_data: list[int]) -> None: ...

    def set_backlight(self, brightness: int) -> None: ...

    def set_rgb(self, r: int, g: int, b: int) -> None: ...

    def set_rgb_fade(self, r_target: int, g_target: int, b_target: int, duration_ms: int = 100) -> None: ...

    def on_button_press(self, callback) -> None: ...

    def on_button_release(self, callback) -> None: ...

    def cleanup(self) -> None: ...


def _load_real_board() -> Optional["WhisplayBoard"]:
    try:
        from ._whisplay_impl import WhisplayBoard  # type: ignore
    except Exception as exc:  # pragma: no cover - executed on dev machines
        logger.warning(
            "Unable to import Whisplay hardware drivers (RPi.GPIO/spidev). "
            "Falling back to mock board. Install pi extras via `uv sync --group pi --all-extras`. "
            "Reason: %s",
            exc,
        )
        return None
    try:
        board = WhisplayBoard()
        logger.info("Initialised Whisplay board (LCD %sx%s)", board.LCD_WIDTH, board.LCD_HEIGHT)
        return board
    except Exception as exc:  # pragma: no cover
        logger.warning("Unable to instantiate real Whisplay board, using mock. Reason: %s", exc)
        return None


@dataclass
class MockBoard:
    LCD_WIDTH: int = 240
    LCD_HEIGHT: int = 280
    CornerHeight: int = 20

    def draw_image(self, x: int, y: int, width: int, height: int, pixel_data: list[int]) -> None:
        logger.debug(
            "Mock draw image at x=%s y=%s w=%s h=%s (payload=%s bytes)",
            x,
            y,
            width,
            height,
            len(pixel_data),
        )

    def set_backlight(self, brightness: int) -> None:
        logger.info("[MOCK] Backlight -> %s%%", brightness)

    def set_rgb(self, r: int, g: int, b: int) -> None:
        logger.info("[MOCK] LED colour -> (%s, %s, %s)", r, g, b)

    def set_rgb_fade(self, r_target: int, g_target: int, b_target: int, duration_ms: int = 100) -> None:
        logger.info(
            "[MOCK] LED fade -> (%s, %s, %s) over %sms", r_target, g_target, b_target, duration_ms
        )
        self.set_rgb(r_target, g_target, b_target)

    def on_button_press(self, callback) -> None:
        logger.debug("[MOCK] on_button_press registered %s", callback)

    def on_button_release(self, callback) -> None:
        logger.debug("[MOCK] on_button_release registered %s", callback)

    def cleanup(self) -> None:
        logger.info("[MOCK] cleanup called")


def create_board(force_mock: bool = False) -> DisplayBoard:
    if force_mock:
        return MockBoard()
    real_board = _load_real_board()
    return real_board or MockBoard()
