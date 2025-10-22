"""
Speech-to-text helpers backed by OpenAI.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from ..config import get_settings
from .openai_client import get_openai_client


class OpenAITranscriber:
    def __init__(self, *, model: str | None = None):
        settings = get_settings()
        self.client = get_openai_client()
        self.model = model or settings.openai_settings.stt_model

    async def transcribe(self, audio_path: Path) -> str:
        audio_path = audio_path.expanduser()
        return await asyncio.to_thread(self._transcribe_sync, audio_path)

    def _transcribe_sync(self, audio_path: Path) -> str:
        with audio_path.open("rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                response_format="text",
            )
        if isinstance(response, str):
            return response.strip()
        return getattr(response, "text", "").strip()
