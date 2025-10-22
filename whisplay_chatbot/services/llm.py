"""
LLM chat helpers for GPT-5-mini.
"""

from __future__ import annotations

import asyncio
from typing import Iterable

from ..config import get_settings
from .openai_client import get_openai_client


class OpenAIChatModel:
    def __init__(self, *, model: str | None = None, temperature: float | None = None):
        settings = get_settings()
        self.client = get_openai_client()
        self.model = model or settings.openai_settings.llm_model
        self.temperature = temperature or settings.openai_settings.response_temperature

    async def complete(self, messages: Iterable[dict]) -> str:
        payload = list(messages)
        response = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=self.model,
            messages=payload,
            temperature=self.temperature,
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""
