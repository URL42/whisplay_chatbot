"""
Runtime assembly helpers for the Whisplay chatbot.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config import ChatbotSettings
from ..core import ChatFlowComponents, ConversationHistory, PersonaManager
from ..hardware import (
    AudioManager,
    ControlManager,
    DisplayController,
    LedAnimator,
    create_board,
)
from ..hardware.board import MockBoard
from ..services import OpenAIChatModel, OpenAITranscriber, OpenAITts


@dataclass(frozen=True)
class RuntimeArtifacts:
    board: object
    components: ChatFlowComponents
    using_mock_board: bool


def build_runtime(settings: ChatbotSettings) -> RuntimeArtifacts:
    board = create_board(force_mock=settings.enable_simulation)
    using_mock_board = isinstance(board, MockBoard)

    display = DisplayController(board)
    led = LedAnimator(board)
    simulate_controls = settings.enable_simulation or using_mock_board
    controls = ControlManager(board, simulate=simulate_controls)
    audio = AudioManager(simulate=settings.enable_simulation or using_mock_board)
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

    return RuntimeArtifacts(board=board, components=components, using_mock_board=using_mock_board)
