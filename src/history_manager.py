from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class GestureEvent:
    gesture: str
    timestamp: datetime

    @property
    def time_text(self) -> str:
        return self.timestamp.strftime("%H:%M:%S")


class HistoryManager:
    def __init__(self, max_entries: int = 30):
        self.max_entries = max(1, max_entries)
        self.events: list[GestureEvent] = []

    def record(self, gesture: str, timestamp: datetime | None = None) -> bool:
        if not gesture or (self.events and self.events[-1].gesture == gesture):
            return False
        self.events.append(GestureEvent(gesture, timestamp or datetime.now()))
        self.events = self.events[-self.max_entries :]
        return True

    def clear(self) -> None:
        self.events.clear()

    def export_csv(self, path: str | Path) -> None:
        with Path(path).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(("timestamp", "gesture"))
            writer.writerows((event.timestamp.isoformat(), event.gesture) for event in self.events)

    def __len__(self) -> int:
        return len(self.events)

