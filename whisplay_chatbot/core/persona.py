"""
Persona selection and fun flavour text helpers.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass
from typing import Iterable, List

from ..config import PersonaConfig, get_default_personas, get_settings
from ..ui_utils import ColorUtils


@dataclass
class PersonaState:
    config: PersonaConfig
    led_color: tuple[int, int, int]


class PersonaManager:
    def __init__(self, personas: Iterable[PersonaConfig] | None = None):
        settings = get_settings()
        self.mode = settings.persona_mode
        self.fixed_name = settings.persona_name

        configs: List[PersonaConfig]
        if personas is not None:
            configs = list(personas)
        else:
            configs = get_default_personas()

        if settings.persona_config_path and settings.persona_config_path.exists():
            import json

            user_configs = json.loads(settings.persona_config_path.read_text())
            for entry in user_configs:
                configs.append(PersonaConfig(**entry))

        if not configs:
            raise ValueError("At least one persona must be configured")

        self.personas = configs
        self._rotator = itertools.cycle(configs)

    def pick(self) -> PersonaState:
        if self.mode == "fixed" and self.fixed_name:
            persona = next(
                (cfg for cfg in self.personas if cfg.name == self.fixed_name),
                self.personas[0],
            )
        elif self.mode == "rotate":
            persona = next(self._rotator)
        else:
            persona = random.choice(self.personas)

        led_color = ColorUtils.get_rgb255_from_any(persona.led_color)
        return PersonaState(config=persona, led_color=led_color)
