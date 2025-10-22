"""
Text-to-speech helper for GPT-5-mini voice.
"""

from __future__ import annotations

import asyncio

from ..config import get_settings
from .openai_client import get_openai_client


class OpenAITts:
    def __init__(self, *, model: str | None = None, voice: str | None = None, format: str = "mp3"):
        settings = get_settings()
        self.client = get_openai_client()
        self.model = model or settings.openai_settings.tts_model
        self.voice = voice or settings.openai_settings.tts_voice
        self.format = format

    async def synthesize(self, text: str) -> bytes:
        return await asyncio.to_thread(self._synthesize_sync, text)

    def _synthesize_sync(self, text: str) -> bytes:
        response = self.client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=text,
            format=self.format,
        )
        if hasattr(response, "read"):
            return response.read()
        if hasattr(response, "content"):
            return response.content
        raise RuntimeError("Unexpected TTS response structure")
