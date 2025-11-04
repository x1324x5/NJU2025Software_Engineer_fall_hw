"""Reminder service: simple dispatcher stub."""
from __future__ import annotations
from typing import Iterable
from ..models import Reminder

class ReminderService:
    def emit(self, reminders: Iterable[Reminder]) -> None:
        for r in reminders:
            if r.enabled:
                print(f"[reminder] {r.at.isoformat()} - {r.message}")
