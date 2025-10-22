"""
Entry point to launch the Whisplay chatbot.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

from .config import get_settings
from .core import ChatFlow, ChatFlowComponents, ConversationHistory, PersonaManager
from .hardware import (
    AudioManager,
    ControlManager,
    DisplayController,
    LedAnimator,
    create_board,
)
from .services import OpenAIChatModel, OpenAITranscriber, OpenAITts

logger = logging.getLogger(__name__)


async def run_chatbot() -> None:
    settings = get_settings()

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    )

    board = create_board(force_mock=settings.enable_simulation)
    display = DisplayController(board)
    led = LedAnimator(board)
    controls = ControlManager(board, simulate=settings.enable_simulation)
    audio = AudioManager(simulate=settings.enable_simulation)
    transcriber = OpenAITranscriber()
    llm = OpenAIChatModel()
    tts = OpenAITts()
    persona_manager = PersonaManager()
    history = ConversationHistory()

    components = ChatFlowComponents(
        display=display,
        controls=controls,
        led=led,
        audio=audio,
        transcriber=transcriber,
        llm=llm,
        tts=tts,
        persona_manager=persona_manager,
        history=history,
        settings=settings,
    )

    chat_flow = ChatFlow(components)

    loop = asyncio.get_running_loop()

    async def shutdown():
        logger.info("Shutting down chatbot...")
        await chat_flow.stop()
        with suppress(Exception):
            board.cleanup()
        for task in asyncio.all_tasks(loop):
            if task is asyncio.current_task(loop):
                continue
            task.cancel()

    for signal_name in ("SIGINT", "SIGTERM"):
        with suppress(AttributeError):
            loop.add_signal_handler(
                getattr(__import__("signal"), signal_name),
                lambda s=signal_name: asyncio.create_task(shutdown()),
            )

    await chat_flow.run()


def main() -> None:
    try:
        asyncio.run(run_chatbot())
    except KeyboardInterrupt:
        print("\nGoodbye from Whisplay! 👋")
