from whisplay_chatbot.config import get_settings


def test_settings_load_defaults(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("WHISPLAY_ENABLE_SIMULATION", "1")
    get_settings.cache_clear()  # type: ignore[attr-defined]
    settings = get_settings()
    assert settings.openai_api_key == "sk-test"
    assert settings.enable_simulation is True
    assert settings.log_level == "INFO"
    assert settings.log_dir.name == "logs"
