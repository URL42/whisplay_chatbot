"""
High-level display controller that keeps the Whisplay LCD updated.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from dataclasses import dataclass, replace
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from ..config import FONT_PATH, LOGO_PATH
from ..ui_utils import ColorUtils, ImageUtils, TextUtils
from .board import DisplayBoard

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class DisplayState:
    status: str = "Idle"
    emoji: str = "😴"
    text: str = "Press the button to chat"
    accent_color: str = "#0064FF"
    battery_level: Optional[int] = None
    battery_color: Optional[str] = None
    brightness: int = 90
    scroll_speed: int = 4
    persona_name: Optional[str] = None


class DisplayController:
    def __init__(
        self,
        board: DisplayBoard,
        fps: int = 25,
        font_path=FONT_PATH,
        logo_path=LOGO_PATH,
    ):
        self.board = board
        self.fps = fps
        self.frame_interval = 1.0 / fps
        self.state = DisplayState()
        self._queue: asyncio.Queue[DisplayState] = asyncio.Queue()
        self._render_task: Optional[asyncio.Task] = None
        self._scroll_offset = 0
        self._last_text = self.state.text
        self.logo_path = logo_path

        font_path = str(font_path)
        self.status_font = ImageFont.truetype(font_path, 28)
        self.emoji_font = ImageFont.truetype(font_path, 40)
        self.battery_font = ImageFont.truetype(font_path, 14)
        self.persona_font = ImageFont.truetype(font_path, 16)
        self.text_utils = TextUtils(font_path=font_path, font_size=20)

        self.logo_image = None
        if logo_path and logo_path.exists():
            from PIL import Image

            self.logo_image = Image.open(logo_path).convert("RGBA")

    async def start(self) -> None:
        if self._render_task:
            return
        self._render_task = asyncio.create_task(self._render_loop())

    async def stop(self) -> None:
        if self._render_task:
            self._render_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._render_task
            self._render_task = None

    async def update(self, **kwargs) -> None:
        new_state = replace(self.state, **kwargs)
        await self._queue.put(new_state)

    async def show_boot_screen(self, duration: float = 1.5) -> None:
        if not self.logo_image:
            return
        # Render logo full screen
        pixel_data = ImageUtils.image_to_rgb565(
            self.logo_image, self.board.LCD_WIDTH, self.board.LCD_HEIGHT
        )
        self.board.draw_image(0, 0, self.board.LCD_WIDTH, self.board.LCD_HEIGHT, pixel_data)
        await asyncio.sleep(duration)

    async def _render_loop(self) -> None:
        try:
            await self.show_boot_screen()
        except Exception:
            logger.debug("Boot screen not available", exc_info=True)

        while True:
            try:
                try:
                    self.state = self._queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass

                if self.state.text != self._last_text:
                    self._scroll_offset = 0
                    self._last_text = self.state.text

                self._render_frame(self.state)
                await asyncio.sleep(self.frame_interval)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error rendering display frame")
                await asyncio.sleep(self.frame_interval)

    def _render_frame(self, state: DisplayState) -> None:
        header_height = 98
        header_img = Image.new("RGBA", (self.board.LCD_WIDTH, header_height), (0, 0, 0, 255))
        header_draw = ImageDraw.Draw(header_img)

        accent_rgb = ColorUtils.get_rgb255_from_any(state.accent_color)
        header_draw.rectangle([(0, 0), (self.board.LCD_WIDTH, header_height)], fill=(0, 0, 0, 255))

        # Status
        status_y = 8
        header_draw.text(
            (self.board.CornerHeight, status_y),
            state.status.upper(),
            font=self.status_font,
            fill=accent_rgb,
        )

        # Persona label
        if state.persona_name:
            header_draw.text(
                (self.board.CornerHeight, status_y + 38),
                f"Persona: {state.persona_name}",
                font=self.persona_font,
                fill=(200, 200, 200),
            )

        # Emoji
        emoji_text = state.emoji or "😊"
        emoji_bbox = self.emoji_font.getbbox(emoji_text)
        emoji_width = emoji_bbox[2] - emoji_bbox[0]
        header_draw.text(
            ((self.board.LCD_WIDTH - emoji_width) // 2, status_y + 10),
            emoji_text,
            font=self.emoji_font,
            fill=(255, 255, 255),
        )

        # Battery gauge
        if state.battery_level is not None:
            self._render_battery(header_draw, state)

        header_rgb565 = ImageUtils.image_to_rgb565(header_img, header_img.width, header_img.height)
        self.board.draw_image(0, 0, header_img.width, header_img.height, header_rgb565)

        # Main text area
        text_area_height = self.board.LCD_HEIGHT - header_height
        text_image = Image.new("RGBA", (self.board.LCD_WIDTH, text_area_height), (0, 0, 0, 255))
        text_draw = ImageDraw.Draw(text_image)

        if state.text:
            lines = self.text_utils.wrap_text(state.text, self.board.LCD_WIDTH - 24)
            line_height = self.text_utils.get_line_height()
            total_height = max(len(lines) * line_height, text_area_height)

            self._scroll_offset = min(self._scroll_offset + state.scroll_speed, total_height)

            offset = self._scroll_offset % max(total_height, 1)
            y_cursor = -offset
            for line in lines:
                if -line_height <= y_cursor <= text_area_height:
                    self.text_utils.draw_mixed_text(
                        text_draw, text_image, line, (12, max(0, y_cursor))
                    )
                y_cursor += line_height

        text_rgb565 = ImageUtils.image_to_rgb565(text_image, text_image.width, text_image.height)
        self.board.draw_image(
            0, header_height, text_image.width, text_image.height, text_rgb565
        )

        self.board.set_backlight(state.brightness)

    def _render_battery(self, draw: ImageDraw.ImageDraw, state: DisplayState) -> None:
        battery_width = 36
        battery_height = 18
        margin_right = 18
        x = self.board.LCD_WIDTH - battery_width - margin_right
        y = 16

        level = max(0, min(100, state.battery_level or 0))
        fill_color = ColorUtils.get_rgb255_from_any(state.battery_color or "#19C3FF")

        draw.rounded_rectangle(
            (x, y, x + battery_width, y + battery_height),
            radius=4,
            outline=(255, 255, 255),
            width=2,
        )
        inner_padding = 3
        fill_width = int((battery_width - inner_padding * 2) * (level / 100))
        draw.rectangle(
            (
                x + inner_padding,
                y + inner_padding,
                x + inner_padding + fill_width,
                y + battery_height - inner_padding,
            ),
            fill=fill_color,
        )
        draw.rectangle(
            (
                x + battery_width,
                y + (battery_height // 2) - 3,
                x + battery_width + 4,
                y + (battery_height // 2) + 3,
            ),
            fill=(255, 255, 255),
        )

        level_text = f"{level}%"
        luminance = ColorUtils.calculate_luminance(fill_color)
        text_color = (0, 0, 0) if luminance > 120 else (255, 255, 255)
        draw.text((x - 42, y + 1), level_text, font=self.battery_font, fill=text_color)
