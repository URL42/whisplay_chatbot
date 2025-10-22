from whisplay_chatbot.core.persona import PersonaManager


def test_persona_selection():
    manager = PersonaManager()
    first = manager.pick()
    assert first.config.name
    assert isinstance(first.led_color, tuple)
    assert len(first.led_color) == 3
