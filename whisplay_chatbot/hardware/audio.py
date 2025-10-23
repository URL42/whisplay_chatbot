"""
Audio capture and playback helpers using SoX and mpg123.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..config import DATA_DIR
from .board import MockBoard

logger = logging.getLogger(__name__)

DEFAULT_RECORD_CMD = ["sox", "-t", "alsa", "default", "-t", "mp3"]
DEFAULT_SILENCE_ARGS = ["silence", "1", "0.1", "60%", "1", "1.0", "60%"]
DEFAULT_PLAY_CMD = ["mpg123", "-", "--scale", "2", "-o", "alsa"]


@dataclass
class ManualRecording:
    process: asyncio.subprocess.Process
    output_path: Path
    future: asyncio.Future[Path]

    def stop(self) -> None:
        if self.process.returncode is None:
            logger.debug("Stopping recording process (pid=%s)", self.process.pid)
            self.process.terminate()
        if not self.future.done():
            self.future.set_result(self.output_path)


class AudioManager:
    def __init__(
        self,
        simulate: bool = False,
        record_cmd: Optional[list[str]] = None,
        play_cmd: Optional[list[str]] = None,
    ):
        self.simulate = simulate
        self.record_cmd = record_cmd or DEFAULT_RECORD_CMD
        self.play_cmd = play_cmd or DEFAULT_PLAY_CMD
        self._current_recording: Optional[ManualRecording] = None

    async def start(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    async def start_manual_recording(self, output_path: Path) -> ManualRecording:
        if self._current_recording:
            self._current_recording.stop()

        loop = asyncio.get_running_loop()
        future: asyncio.Future[Path] = loop.create_future()

        cmd = [*self.record_cmd, str(output_path)]
        logger.info("Starting recording: %s", " ".join(cmd))
        process = await asyncio.create_subprocess_exec(
            *cmd, stderr=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE
        )

        # Monitor process completion
        async def _watch():
            await process.wait()
            if process.returncode not in (0, None):
                stderr = await process.stderr.read() if process.stderr else b""
                logger.warning("Recording ended with code %s: %s", process.returncode, stderr)
            if not future.done():
                future.set_result(output_path)

        asyncio.create_task(_watch())

        recording = ManualRecording(process=process, output_path=output_path, future=future)
        self._current_recording = recording
        return recording

    async def play_startup_chime(self) -> None:
        if self.simulate:
            logger.info("[SIM] Startup chime skipped (simulation mode)")
            return

        cmd = [
            "sox",
            "-n",
            "-t",
            "alsa",
            "default",
            "synth",
            "0.35",
            "sin",
            "880",
            "fade",
            "q",
            "0.02",
            "0.35",
            "0.1",
        ]
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            logger.debug("SoX not available; skipping startup chime")
            return

        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            logger.debug(
                "Startup chime failed (code=%s): %s",
                process.returncode,
                (stderr or b"").decode(errors="ignore"),
            )
        else:
            if stdout:
                logger.debug("Startup chime stdout: %s", stdout.decode(errors="ignore"))

    async def record_with_timeout(self, output_path: Path, max_duration: int) -> Path:
        recording = await self.start_manual_recording(output_path)
        try:
            return await asyncio.wait_for(recording.future, timeout=max_duration)
        except asyncio.TimeoutError:
            recording.stop()
            return output_path

    async def play_audio(self, audio_bytes: bytes, simulate_dump: bool = True) -> None:
        if self.simulate:
            if simulate_dump:
                outfile = DATA_DIR / "tts-preview.mp3"
                outfile.write_bytes(audio_bytes)
                logger.info("[SIM] Saved TTS preview to %s", outfile)
            return

        process = await asyncio.create_subprocess_exec(
            *self.play_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        assert process.stdin is not None
        process.stdin.write(audio_bytes)
        await process.stdin.drain()
        process.stdin.close()
        await process.wait()

        if process.returncode != 0:
            stderr = await process.stderr.read() if process.stderr else b""
            logger.warning("mpg123 exited with code %s: %s", process.returncode, stderr)


def create_audio_manager(board, simulate: bool) -> AudioManager:
    return AudioManager(simulate=simulate or isinstance(board, MockBoard))
