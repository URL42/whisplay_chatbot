"""
Helpers for rendering text and emoji on the Whisplay LCD.
"""

from __future__ import annotations

import unicodedata
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Iterable, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cairosvg

from .config import EMOJI_DIR


class ColorUtils:
    @staticmethod
    def rgb565_to_rgb255(color_565: int) -> tuple[int, int, int]:
        red_5bit = (color_565 >> 11) & 0x1F
        green_6bit = (color_565 >> 5) & 0x3F
        blue_5bit = color_565 & 0x1F
        red_8bit = (red_5bit * 255) // 31
        green_8bit = (green_6bit * 255) // 63
        blue_8bit = (blue_5bit * 255) // 31
        return red_8bit, green_8bit, blue_8bit

    @staticmethod
    def hex_to_rgb255(hex_color: str) -> tuple[int, int, int]:
        hex_color = hex_color.lstrip("#")
        if len(hex_color) not in (6, 8):
            raise ValueError(f"Invalid hex colour {hex_color}")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return r, g, b

    @staticmethod
    def get_rgb255_from_any(value: str | int | tuple[int, int, int]) -> tuple[int, int, int]:
        if isinstance(value, tuple):
            return value
        if isinstance(value, int):
            return ColorUtils.rgb565_to_rgb255(value)
        return ColorUtils.hex_to_rgb255(value)

    @staticmethod
    def calculate_luminance(rgb_tuple: tuple[int, int, int]) -> float:
        r, g, b = rgb_tuple
        return 0.299 * r + 0.587 * g + 0.114 * b


class ImageUtils:
    @staticmethod
    def image_to_rgb565(image: Image.Image, width: int, height: int) -> list[int]:
        image = image.convert("RGB")
        image.thumbnail((width, height), Image.LANCZOS)
        bg = Image.new("RGB", (width, height), (0, 0, 0))
        x = (width - image.width) // 2
        y = (height - image.height) // 2
        bg.paste(image, (x, y))

        np_img = np.array(bg)
        r = (np_img[:, :, 0] >> 3).astype(np.uint16)
        g = (np_img[:, :, 1] >> 2).astype(np.uint16)
        b = (np_img[:, :, 2] >> 3).astype(np.uint16)

        rgb565 = (r << 11) | (g << 5) | b
        high_byte = (rgb565 >> 8).astype(np.uint8)
        low_byte = (rgb565 & 0xFF).astype(np.uint8)
        interleaved = np.dstack((high_byte, low_byte)).flatten().tolist()
        return interleaved


class EmojiUtils:
    @staticmethod
    @lru_cache(maxsize=512)
    def emoji_to_filename(char: str) -> Path:
        return EMOJI_DIR / ("-".join(f"{ord(c):x}" for c in char) + ".svg")

    @staticmethod
    def get_local_emoji_svg_image(char: str, size: int) -> Image.Image | None:
        if not EMOJI_DIR.exists():
            return None
        path = EmojiUtils.emoji_to_filename(char)
        if not path.exists():
            return None
        try:
            png_bytes = cairosvg.svg2png(url=str(path), output_width=size, output_height=size)
            return Image.open(BytesIO(png_bytes)).convert("RGBA")
        except Exception:
            return None

    @staticmethod
    def is_emoji(char: str) -> bool:
        return unicodedata.category(char) in {"So", "Sk"} or ord(char) > 0x1F000


@lru_cache(maxsize=2048)
def _get_char_size(font_hash: Tuple[str, int], char: str) -> tuple[int, int]:
    font = ImageFont.truetype(font_hash[0], font_hash[1])
    if EmojiUtils.is_emoji(char):
        emoji_img = EmojiUtils.get_local_emoji_svg_image(char, size=font.size)
        if emoji_img:
            return emoji_img.width, emoji_img.height
    bbox = font.getbbox(char)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


class TextUtils:
    def __init__(self, font_path: str | Path, font_size: int):
        self.font_path = Path(font_path)
        self.font_size = font_size
        self.font = ImageFont.truetype(str(self.font_path), font_size)

    def get_char_size(self, char: str) -> tuple[int, int]:
        return _get_char_size((str(self.font_path), self.font_size), char)

    def draw_mixed_text(self, draw: ImageDraw.ImageDraw, image: Image.Image, text: str, start_xy):
        x, y = start_xy
        line_image = self.get_line_image(text)
        image.paste(line_image, (x, y), line_image)

    @lru_cache(maxsize=1024)
    def get_line_image(self, text: str) -> Image.Image:
        ascent, descent = self.font.getmetrics()
        baseline = ascent
        line_height = ascent + descent
        width = sum(self.get_char_size(ch)[0] for ch in text)
        img = Image.new("RGBA", (max(width, 1), line_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cursor_x = 0
        for char in text:
            if EmojiUtils.is_emoji(char):
                emoji_img = EmojiUtils.get_local_emoji_svg_image(char, size=self.font.size)
                if emoji_img:
                    emoji_y = baseline - emoji_img.height
                    img.paste(emoji_img, (cursor_x, emoji_y), emoji_img)
                    cursor_x += emoji_img.width
                    continue
            draw.text((cursor_x, 0), char, font=self.font, fill=(255, 255, 255, 255))
            cursor_x += self.get_char_size(char)[0]
        return img

    def wrap_text(self, text: str, max_width: int) -> list[str]:
        lines: list[str] = []
        current_line = ""
        current_width = 0

        for char in text:
            char_width = self.get_char_size(char)[0]
            if current_width + char_width <= max_width:
                current_line += char
                current_width += char_width
            else:
                if current_line:
                    lines.append(current_line)
                current_line = char
                current_width = char_width
        if current_line:
            lines.append(current_line)
        return lines

    def get_line_height(self) -> int:
        ascent, descent = self.font.getmetrics()
        return ascent + descent
