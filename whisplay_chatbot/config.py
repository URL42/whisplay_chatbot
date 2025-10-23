"""
Configuration helpers for the Whisplay chatbot.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, PositiveInt, validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASSET_DIR = PROJECT_ROOT / "assets"
LEGACY_ASSET_DIR = PROJECT_ROOT / "python"  # backwards compat for older layouts
DEFAULT_EMOJI_DIR = DEFAULT_ASSET_DIR / "emoji_svg"

FONT_CANDIDATES = [
    DEFAULT_ASSET_DIR / "fonts" / "NotoSans-Regular.ttf",
    Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
]

LOGO_CANDIDATES = [
    DEFAULT_ASSET_DIR / "img" / "logo.png",
    LEGACY_ASSET_DIR / "img" / "logo.png",
]


def _resolve_first_existing(paths: list[Path]) -> Path:
    for path in paths:
        if path.exists():
            return path
    return paths[0]


ASSET_DIR = DEFAULT_ASSET_DIR
EMOJI_DIR = (
    DEFAULT_EMOJI_DIR if DEFAULT_EMOJI_DIR.exists() else LEGACY_ASSET_DIR / "emoji_svg"
)
FONT_PATH = _resolve_first_existing(FONT_CANDIDATES)
LOGO_PATH = _resolve_first_existing(LOGO_CANDIDATES)
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = DATA_DIR / "logs"


class PersonaConfig(BaseModel):
    name: str
    description: str
    system_prompt: str
    led_color: tuple[int, int, int] = (0, 64, 255)
    accent_color: str = "#0000FF"


class OpenAISettings(BaseModel):
    api_key: str
    base_url: Optional[HttpUrl] = None
    llm_model: str = "gpt-5-mini"
    stt_model: str = "gpt-5-mini-transcribe"
    tts_model: str = "gpt-5-mini-tts"
    tts_voice: str = "alloy"
    response_temperature: float = 0.6


class ChatbotSettings(BaseSettings):
    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    openai_base_url: Optional[str] = Field(default=None, alias="OPENAI_BASE_URL")
    tts_voice: str = Field(default="alloy", alias="WHISPLAY_TTS_VOICE")
    persona_mode: Literal["random", "rotate", "fixed"] = Field(
        default="random", alias="WHISPLAY_PERSONA_MODE"
    )
    persona_name: Optional[str] = Field(default=None, alias="WHISPLAY_PERSONA_NAME")
    max_record_seconds: PositiveInt = Field(
        default=12, alias="WHISPLAY_MAX_RECORD_SECONDS"
    )
    idle_timeout_seconds: PositiveInt = Field(
        default=180, alias="WHISPLAY_IDLE_TIMEOUT_SECONDS"
    )
    enable_simulation: bool = Field(default=False, alias="WHISPLAY_ENABLE_SIMULATION")
    persona_config_path: Optional[Path] = Field(
        default=None, alias="WHISPLAY_PERSONAS_PATH"
    )
    fun_fact_url: Optional[str] = Field(default=None, alias="WHISPLAY_FUN_FACT_URL")
    log_level: str = Field(default="INFO", alias="WHISPLAY_LOG_LEVEL")
    log_dir: Path = Field(default=LOG_DIR, alias="WHISPLAY_LOG_DIR")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @validator("persona_config_path")
    def _expand_persona_path(cls, value: Optional[Path]) -> Optional[Path]:
        if value is None:
            return value
        return Path(value).expanduser()

    @validator("log_dir")
    def _expand_log_dir(cls, value: Path) -> Path:
        return Path(value).expanduser()

    @property
    def openai_settings(self) -> OpenAISettings:
        return OpenAISettings(
            api_key=self.openai_api_key,
            base_url=self.openai_base_url,
            tts_voice=self.tts_voice,
        )


@lru_cache
def get_settings() -> ChatbotSettings:
    settings = ChatbotSettings()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    return settings


def get_default_personas() -> list[PersonaConfig]:
    return [
        PersonaConfig(
            name="Arcade Ally",
            description="Retro gamer with a joyful, high-energy vibe",
            system_prompt=(
                "You are Arcade Ally, a playful AI with a love for retro games, 8-bit music, "
                "and surprise power-ups. Your replies should be encouraging, short, and packed "
                "with gaming metaphors. Always sign off with a quick onomatopoeic effect "
                "like 'pew!' or 'kaboom!'."
            ),
            led_color=(0, 64, 255),
            accent_color="#19C3FF",
        ),
        PersonaConfig(
            name="Cosmic Companion",
            description="Dreamy space guide who shares celestial lore",
            system_prompt=(
                "You are Cosmic Companion, a gentle storyteller who speaks in cosmic imagery "
                "and poetic metaphors. You sneak in a whimsical space fact, real or speculative, "
                "in each reply. Close responses with a soft emoji that evokes stargazing."
            ),
            led_color=(138, 43, 226),
            accent_color="#8A2BE2",
        ),
        PersonaConfig(
            name="Byte-Sized Bard",
            description="Charming pun-loving poet with dynamic rhymes",
            system_prompt=(
                "You are the Byte-Sized Bard, a lighthearted poet that weaves puns and "
                "rhyming couplets into concise answers. Keep the humor cozy, with a wink "
                "toward technology or everyday absurdities."
            ),
            led_color=(255, 140, 0),
            accent_color="#FF8C00",
        ),
    ]
