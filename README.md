# Whisplay Chatbot (All Python Edition)

Turn a Raspberry Pi Zero 2 W + PiSugar Whisplay HAT into a pocketable AI buddy.  
Hold the button, speak your mind, and the bot answers back with a playful persona, animated LEDs, scrolling text, and synthesized voice powered by OpenAI GPT-5-mini.

> ⚠️ Fun project only. This is not a safety-critical device or a financial oracle.

---

## Hardware

- Raspberry Pi Zero 2 W (Raspbian/Raspberry Pi OS Bookworm recommended)
- PiSugar Whisplay HAT (LCD, mic, speaker, RGB LED, button)
- Optional: PiSugar battery pack (not required for development/simulation)
- MicroSD card (16 GB+) and reliable 5 V power source

---

## Project Highlights

- **Single-language stack** – Pure Python (`asyncio` everywhere) with uv/`pyproject.toml`.
- **Personality engine** – Three built-in personas (Arcade Ally, Cosmic Companion, Byte-Sized Bard) with LED colour themes and playful prompts.
- **Fun idle loop** – Periodic hints and tips when the device is waiting for your next question.
- **Speech pipeline** – SoX for capture, OpenAI GPT-5-mini for STT/LLM/TTS, mpg123 for playback.
- **Simulation mode** – Run the full flow on macOS/Linux dev machines (keyboard triggers replace the Whisplay button).
- **History & continuity** – Recent conversations stored under `data/history.json` to give replies some memory.

---

## Quickstart (Simulation Mode)

```bash
uv sync --all-extras
cp .env.example .env
echo "OPENAI_API_KEY=sk-your-key" >> .env
uv run -- whisplay-chatbot simulate
```

Press `Enter` once to simulate a button press, then again to release. Logs are written to `data/logs/whisplay.log`; follow them with `tail -f data/logs/whisplay.log`. Simulation audio dumps land in `data/`.

---

## Installing on Raspberry Pi

1. **Prepare the Pi**
   ```bash
   sudo apt update
   sudo apt install -y python3.11-full python3-pip sox mpg123 git
   ```

2. **Clone & install**
   ```bash
   git clone https://github.com/URL42/whisplay_chatbot.git
   cd whisplay_chatbot
   uv sync --group pi --all-extras
   ```

3. **Environment**
   ```bash
   cp .env.example .env
   nano .env   # add OpenAI key and any overrides
   ```

4. **Run**
   ```bash
   uv run -- whisplay-chatbot run
   # or: uv run -- python -m whisplay_chatbot.main run
   ```

Hold the Whisplay button, speak, release, and enjoy! Add `--simulate` to the command if you need to force keyboard mode.

> Tip: Logs are stored in `data/logs/whisplay.log`. Stream them with `tail -f data/logs/whisplay.log`.

---

## Systemd Service (Headless Boot)

Create `/etc/systemd/system/whisplay-chatbot.service`:

```ini
[Unit]
Description=Whisplay AI Chatbot
After=network-online.target sound.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/whisplay_chatbot
EnvironmentFile=/home/pi/whisplay_chatbot/.env
ExecStart=/home/pi/.local/bin/uv run -- whisplay-chatbot run
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now whisplay-chatbot
```

Logs stream under `journalctl -u whisplay-chatbot -f`.

---

## Configuration

| Variable | Description | Default |
| --- | --- | --- |
| `OPENAI_API_KEY` | GPT-5-mini API key | **required** |
| `OPENAI_BASE_URL` | Override API endpoint (optional) | |
| `WHISPLAY_ENABLE_SIMULATION` | `1` to run without Pi hardware | `0` |
| `WHISPLAY_PERSONA_MODE` | `random`, `rotate`, or `fixed` | `random` |
| `WHISPLAY_PERSONA_NAME` | Persona name if `fixed` | |
| `WHISPLAY_IDLE_TIMEOUT_SECONDS` | Hint cadence while idle | `180` |
| `WHISPLAY_MAX_RECORD_SECONDS` | Recording cap | `12` |
| `WHISPLAY_TTS_VOICE` | Preferred OpenAI voice for playback | `alloy` |
| `WHISPLAY_LOG_LEVEL` | Logging verbosity | `INFO` |
| `WHISPLAY_LOG_DIR` | Directory for log files | `data/logs` |

Place any custom persona definitions in a JSON file and point `WHISPLAY_PERSONAS_PATH` to it.

---

## Development & Testing

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

To run the chatbot with live hardware from your dev machine, set `WHISPLAY_ENABLE_SIMULATION=0` and ensure you have the Whisplay HAT drivers (`RPi.GPIO`, `spidev`) available.

---

## Fun Experiments

- Ask “Tell me a retro joke” to trigger Arcade Ally puns.
- Try “Narrate a space bedtime story” for stargazing lore.
- Request haiku or limericks to hear the Byte-Sized Bard rhyme.
- Leave the bot idle to get playful tips on what to ask next.

---

## License

GPL-3.0-or-later — see [`LICENSE`](LICENSE). Contributions welcome! Open a PR with your persona ideas, idle animations, or new hardware tricks.
