"""
Tiny persistence for recent conversations.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

from ..config import DATA_DIR


@dataclass
class HistoryEntry:
    persona: str
    user_text: str
    bot_text: str


class ConversationHistory:
    def __init__(self, history_file: Path | None = None, max_entries: int = 20):
        self.max_entries = max_entries
        self.history_file = history_file or DATA_DIR / "history.json"
        self.entries: List[HistoryEntry] = []
        self._load()

    def _load(self) -> None:
        if not self.history_file.exists():
            return
        try:
            raw_entries = json.loads(self.history_file.read_text())
        except json.JSONDecodeError:
            return
        for entry in raw_entries[-self.max_entries :]:
            self.entries.append(HistoryEntry(**entry))

    def append(self, entry: HistoryEntry) -> None:
        self.entries.append(entry)
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries :]
        self._persist()

    def _persist(self) -> None:
        payload = [asdict(entry) for entry in self.entries]
        self.history_file.write_text(json.dumps(payload, indent=2))

    def as_context(self) -> str:
        if not self.entries:
            return ""
        return "\n".join(
            f"{entry.persona} heard '{entry.user_text}' and replied '{entry.bot_text}'"
            for entry in self.entries[-5:]
        )
