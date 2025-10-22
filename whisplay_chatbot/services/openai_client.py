"""
Shared OpenAI client factory with caching.
"""

from __future__ import annotations

from functools import lru_cache

from openai import OpenAI

from ..config import get_settings


@lru_cache
def get_openai_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )
