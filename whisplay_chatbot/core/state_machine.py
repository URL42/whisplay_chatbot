"""
Async state machine that powers the Whisplay chatbot experience.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..config import ChatbotSettings, DATA_DIR
from ..hardware import (
    AudioManager,
    ControlManager,
    DisplayController,
    DisplayState,
    LedAnimator,
)
from ..services import OpenAIChatModel, OpenAITranscriber, OpenAITts
from .history import ConversationHistory, HistoryEntry
from .persona import PersonaManager, PersonaState


logger = logging.getLogger(__name__)


FUN_IDLE_LINES = [
    "Hold the talk button for secret missions!",
    "Tip: whisper a movie quote for a surprise response.",
    "Feeling brave? Ask for a haiku about coffee beans.",
    "Pro tip: short questions get snappier replies.",
    "Need ideas? Try 'tell me a retro game fact'.",
]


@dataclass
class ChatFlowComponents:
    display: DisplayController
    controls: ControlManager
    led: LedAnimator
    audio: AudioManager
    transcriber: OpenAITranscriber
    llm: OpenAIChatModel
    tts: OpenAITts
    persona_manager: PersonaManager
    history: ConversationHistory
    settings: ChatbotSettings


class ChatFlow:
    def __init__(self, components: ChatFlowComponents):
        self.components = components
        self._running = False
        self._idle_hint_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        if self._running:
            return
        self._running = True

        await self.components.display.start()
        await self.components.display.update(
            status="Booting",
            emoji="🤖",
            text="Whisplay is warming up. Get ready to press the button!",
            accent_color="#19C3FF",
            brightness=90,
            scroll_speed=2,
        )
        await self.components.led.set_state((25, 120, 255), mode="pulse")

        await self.components.led.start()
        await self.components.controls.start()
        await self.components.audio.start()
        await self._play_startup_chime()
        logger.info("Startup complete; waiting for button press")

    async def _play_startup_chime(self) -> None:
        try:
            await self.components.audio.play_startup_chime()
        except Exception:  # pragma: no cover - chime is best-effort
            logger.debug("Startup chime errored", exc_info=True)

    async def run(self) -> None:
        await self.start()

        try:
            while True:
                persona_state = self.components.persona_manager.pick()
                await self._enter_idle(persona_state)
                audio_path = await self._record_interaction(persona_state)
                if audio_path is None:
                    continue
                user_text = await self._transcribe_audio(audio_path, persona_state)
                if not user_text:
                    await self._notify_user_speech_not_detected(persona_state)
                    continue
                await self._process_answer(persona_state, user_text)
        except asyncio.CancelledError:
            raise
        finally:
            await self.stop()

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._idle_hint_task:
            self._idle_hint_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._idle_hint_task
            self._idle_hint_task = None

    async def _enter_idle(self, persona: PersonaState) -> None:
        display_state = DisplayState(
            status="Idle",
            emoji="😴",
            text=random.choice(FUN_IDLE_LINES),
            accent_color=persona.config.accent_color,
            brightness=85,
            persona_name=persona.config.name,
            scroll_speed=3,
        )
        await self.components.display.update(**display_state.__dict__)
        await self.components.led.set_state(persona.led_color, mode="breathing")

        if self._idle_hint_task:
            self._idle_hint_task.cancel()

        self._idle_hint_task = asyncio.create_task(self._idle_hint_loop(persona))

    async def _idle_hint_loop(self, persona: PersonaState) -> None:
        settings = self.components.settings
        try:
            while True:
                await asyncio.sleep(settings.idle_timeout_seconds)
                await self.components.display.update(
                    text=random.choice(FUN_IDLE_LINES),
                    emoji="💡",
                    status="Ready",
                    accent_color=persona.config.accent_color,
                )
        except asyncio.CancelledError:
            return

    async def _record_interaction(self, persona: PersonaState) -> Optional[Path]:
        settings = self.components.settings

        await self.components.display.update(
            status="Listening",
            emoji="🎤",
            text="Hold the button and speak...",
            accent_color=persona.config.accent_color,
            brightness=95,
            scroll_speed=2,
        )
        await self.components.led.set_state((0, 200, 70), mode="pulse")

        await self.components.controls.wait_for_press()

        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        audio_path = DATA_DIR / f"user-{timestamp}.mp3"

        recording = await self.components.audio.start_manual_recording(audio_path)

        try:
            await self.components.controls.wait_for_release()
        finally:
            recording.stop()

        try:
            return await asyncio.wait_for(
                recording.future, timeout=settings.max_record_seconds
            )
        except asyncio.TimeoutError:
            return audio_path

    async def _transcribe_audio(self, audio_path: Path, persona: PersonaState) -> str:
        await self.components.display.update(
            status="Transcribing",
            emoji="🧠",
            text="Thinking about what you said...",
            accent_color=persona.config.accent_color,
            scroll_speed=3,
        )
        await self.components.led.set_state((255, 140, 0), mode="sparkle")
        try:
            return await self.components.transcriber.transcribe(audio_path)
        except Exception:
            await self.components.display.update(
                status="Error",
                emoji="⚠️",
                text="Sorry, I couldn't understand that audio. Try again?",
                accent_color="#FF4F6D",
            )
            return ""

    async def _notify_user_speech_not_detected(self, persona: PersonaState) -> None:
        await self.components.display.update(
            status="Listening",
            emoji="🤔",
            text="I didn't catch anything. Hold the button and speak again!",
            accent_color=persona.config.accent_color,
            scroll_speed=3,
        )
        await asyncio.sleep(2)

    async def _process_answer(self, persona: PersonaState, user_text: str) -> None:
        history_context = self.components.history.as_context()

        system_prompt = persona.config.system_prompt
        if history_context:
            system_prompt += (
                "\n\nRecent conversations to keep continuity:\n"
                f"{history_context}"
            )
        system_prompt += (
            "\n\nRespond in 2-4 energetic sentences. Include at least one playful emoji "
            "and keep replies under 280 characters."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ]

        await self.components.display.update(
            status="Thinking",
            emoji="🤖",
            text=random.choice(
                [
                    "Plotting a clever reply...",
                    "Crunching galactic data...",
                    "Cooking up something fun...",
                ]
            ),
            accent_color=persona.config.accent_color,
            scroll_speed=4,
        )
        await self.components.led.set_state((255, 128, 0), mode="sparkle")

        try:
            bot_text = await self.components.llm.complete(messages)
        except Exception as exc:
            await self.components.display.update(
                status="Error",
                emoji="😵",
                text=f"Oh no, I glitched: {exc}",
                accent_color="#FF4F6D",
            )
            await asyncio.sleep(3)
            return

        await self.components.display.update(
            status="Answering",
            emoji="💬",
            text=bot_text,
            accent_color=persona.config.accent_color,
            scroll_speed=5,
        )

        await self.components.led.set_state(persona.led_color, mode="pulse")

        try:
            audio_bytes = await self.components.tts.synthesize(bot_text)
            await self.components.audio.play_audio(audio_bytes)
        except Exception:
            await self.components.display.update(
                status="Mute Mode",
                emoji="🔇",
                text=f"{bot_text}\n\n(Voice synth failed, so text only!)",
                accent_color="#FF4F6D",
            )

        self.components.history.append(
            HistoryEntry(
                persona=persona.config.name,
                user_text=user_text,
                bot_text=bot_text,
            )
        )

        await self.components.display.update(
            status="Complete",
            emoji="✅",
            text="Hold the button when you're ready for another round!",
            accent_color=persona.config.accent_color,
            scroll_speed=3,
        )
        await self.components.led.set_state(persona.led_color, mode="breathing")
