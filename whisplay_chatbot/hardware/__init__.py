"""Hardware abstraction layer for Whisplay chatbot."""

from .board import create_board
from .display import DisplayController, DisplayState
from .audio import AudioManager
from .controls import ControlManager
from .led import LedAnimator

__all__ = [
    "create_board",
    "DisplayController",
    "DisplayState",
    "AudioManager",
    "ControlManager",
    "LedAnimator",
]
